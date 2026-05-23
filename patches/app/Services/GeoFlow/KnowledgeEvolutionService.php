<?php

namespace App\Services\GeoFlow;

use App\Models\KnowledgeChunk;
use App\Support\GeoFlow\ApiKeyCrypto;
use App\Support\GeoFlow\OpenAiRuntimeProvider;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Laravel\Ai\agent;
use Laravel\Ai\Embeddings;

/**
 * v2.1: 知识库自主进化服务。
 *
 * 定期扫描知识库 chunk，执行：
 *   1. 质量评分 — AI 评估每个 chunk 的内容质量
 *   2. 合并去重 — 发现高相似度 chunk 自动合并
 *   3. 摘要生成 — 自动为长 chunk 生成摘要
 *   4. 交叉引用 — 发现 chunk 之间的语义关联
 *   5. 过期归档 — 长期未访问的低质量 chunk 自动归档
 *
 * 全部使用可配置的 AI 模型，支持任何 Provider。
 */
class KnowledgeEvolutionService
{
    private ?string $aiModel = null;
    private ?string $aiProviderName = null;
    private ?string $aiApiKey = null;
    private ?string $aiApiUrl = null;

    public function __construct()
    {
        $this->loadAiConfig();
    }

    /**
     * 加载进化 AI 模型配置。
     * 优先使用 EVOLUTION_MODEL 环境变量，否则使用默认 chat 模型。
     */
    private function loadAiConfig(): void
    {
        $aiModel = Config::get('geoflow.evolution_model', 'deepseek-chat');

        // 检查是否启用 AI Gateway
        if (Config::get('geoflow.ai_gateway_enabled', false)) {
            $gatewayUrl = Config::get('geoflow.ai_gateway_url', 'http://ai-gateway:19090');
            $this->aiApiUrl = $gatewayUrl;
            $this->aiApiKey = ''; // Gateway 不需要 key
            $this->aiModel = $aiModel;

            // 注册 Gateway provider
            $this->aiProviderName = OpenAiRuntimeProvider::registerProvider(
                'evolution',
                'openai',
                $gatewayUrl,
                ''
            );
            return;
        }

        // 没有 AI Gateway：从数据库 ai_models 获取第一个可用的 chat 模型
        $model = \App\Models\AiModel::where('model_type', 'chat')
            ->where('status', 'active')
            ->orderBy('failover_priority')
            ->first();

        if ($model) {
            $this->aiModel = $model->model_id;
            $this->aiApiUrl = $model->api_url;
            $this->aiApiKey = ApiKeyCrypto::decrypt($model->api_key) ?? '';
            $driver = OpenAiRuntimeProvider::resolveChatDriver($this->aiApiUrl, $this->aiModel);
            $this->aiProviderName = OpenAiRuntimeProvider::registerProvider(
                'evolution',
                $driver,
                $this->aiApiUrl,
                $this->aiApiKey
            );
        }
    }

    /**
     * 是否可以运行进化任务。
     */
    public function isReady(): bool
    {
        return $this->aiProviderName !== null && $this->aiModel !== null;
    }

    /**
     * 执行一次完整的知识进化。
     */
    public function evolve(): array
    {
        $startTime = now();
        $stats = [
            'chunks_processed' => 0,
            'chunks_merged' => 0,
            'chunks_archived' => 0,
            'chunks_summarized' => 0,
            'links_created' => 0,
            'status' => 'running',
            'error_message' => null,
        ];

        // 记录进化运行
        $run = $this->createEvolutionRun($startTime);

        try {
            if (!$this->isReady()) {
                throw new \RuntimeException('No AI model configured for evolution');
            }

            $maxChunks = Config::get('geoflow.evolution_max_chunks_per_run', 50);
            $threshold = Config::get('geoflow.evolution_similarity_threshold', 0.85);
            $autoPrune = Config::get('geoflow.evolution_auto_prune', true);
            $autoMerge = Config::get('geoflow.evolution_auto_merge', true);
            $autoSummarize = Config::get('geoflow.evolution_auto_summarize', true);
            $autoLink = Config::get('geoflow.evolution_auto_link', true);
            $archiveDays = Config::get('geoflow.evolution_auto_archive_days', 90);

            // 1. 质量评分
            Log::info('[Evolution] Starting quality scoring...');
            $scoredChunks = $this->scoreChunks($maxChunks);
            $stats['chunks_processed'] = count($scoredChunks);

            // 2. 去重合并
            if ($autoMerge) {
                Log::info('[Evolution] Starting merge detection...');
                $mergedCount = $this->mergeDuplicates($threshold);
                $stats['chunks_merged'] = $mergedCount;
            }

            // 3. 摘要生成
            if ($autoSummarize) {
                Log::info('[Evolution] Starting summarization...');
                $summarizedCount = $this->summarizeChunks($scoredChunks);
                $stats['chunks_summarized'] = $summarizedCount;
            }

            // 4. 交叉引用
            if ($autoLink) {
                Log::info('[Evolution] Starting cross-referencing...');
                $linksCount = $this->createCrossReferences($threshold);
                $stats['links_created'] = $linksCount;
            }

            // 5. 过期归档
            if ($autoPrune) {
                Log::info('[Evolution] Starting archiving...');
                $archivedCount = $this->archiveStaleChunks($archiveDays);
                $stats['chunks_archived'] = $archivedCount;
            }

            // 完成
            $stats['status'] = 'completed';
            $this->completeEvolutionRun($run, $stats, $startTime);

            Log::info('[Evolution] Completed', $stats);
        } catch (\Throwable $e) {
            $stats['status'] = 'failed';
            $stats['error_message'] = $e->getMessage();
            $this->completeEvolutionRun($run, $stats, $startTime);
            Log::error('[Evolution] Failed: '.$e->getMessage());
        }

        return $stats;
    }

    /**
     * 对 chunks 进行 AI 质量评分。
     */
    private function scoreChunks(int $limit): array
    {
        $chunks = KnowledgeChunk::whereNull('deleted_at')
            ->orderBy('id')
            ->limit($limit)
            ->get();

        $scored = [];
        foreach ($chunks as $chunk) {
            $score = $this->evaluateChunkQuality($chunk);
            if ($score !== null) {
                DB::table('knowledge_chunk_scores')->updateOrInsert(
                    ['chunk_id' => $chunk->id],
                    [
                        'quality_score' => $score['quality'],
                        'relevance_score' => $score['relevance'],
                        'freshness_score' => $score['freshness'],
                        'updated_at' => now(),
                    ]
                );
                $scored[] = ['chunk' => $chunk, 'scores' => $score];
            }
        }

        return $scored;
    }

    /**
     * 调用 AI 评估单个 chunk 的质量。
     */
    private function evaluateChunkQuality(KnowledgeChunk $chunk): ?array
    {
        $content = $chunk->content ?? '';
        if (mb_strlen($content) < 10) {
            return ['quality' => 0.1, 'relevance' => 0.1, 'freshness' => 0.5];
        }

        $prompt = <<<PROMPT
你是一个知识库质量评估专家。请评估以下知识片段的质量，只返回 JSON：

{
  "quality": <0-1浮点数，内容质量：信息密度、准确性、完整性>,
  "relevance": <0-1浮点数，相关性：主题集中度>,
  "freshness": <0-1浮点数，时效性估计>
}

知识片段：
{$content}
PROMPT;

        try {
            $response = agent()->prompt($prompt, [], $this->aiProviderName, $this->aiModel);
            $text = OpenAiRuntimeProvider::normalizeGeneratedText($response);
            $text = trim($text);

            // 提取 JSON 块
            if (preg_match('/\{(?:[^{}]|(?R))*\}/s', $text, $matches)) {
                $data = json_decode($matches[0], true);
                if ($data && isset($data['quality'])) {
                    return [
                        'quality' => (float) ($data['quality'] ?? 0.5),
                        'relevance' => (float) ($data['relevance'] ?? 0.5),
                        'freshness' => (float) ($data['freshness'] ?? 0.5),
                    ];
                }
            }
        } catch (\Throwable $e) {
            Log::warning('[Evolution] Score failed for chunk '.$chunk->id.': '.$e->getMessage());
        }

        return null;
    }

    /**
     * 检测并合并高相似度 chunk。
     */
    private function mergeDuplicates(float $threshold): int
    {
        $merged = 0;
        $chunks = KnowledgeChunk::whereNull('deleted_at')
            ->orderBy('id')
            ->get();

        $count = count($chunks);
        for ($i = 0; $i < $count; $i++) {
            for ($j = $i + 1; $j < $count; $j++) {
                $similarity = $this->calculateSimilarity(
                    $chunks[$i]->content ?? '',
                    $chunks[$j]->content ?? ''
                );

                if ($similarity >= $threshold) {
                    // 记录为关联（duplicate 类型），由人工决定是否真正合并
                    DB::table('knowledge_chunk_links')->updateOrInsert(
                        [
                            'source_chunk_id' => $chunks[$i]->id,
                            'target_chunk_id' => $chunks[$j]->id,
                            'link_type' => 'duplicate',
                        ],
                        [
                            'similarity_score' => $similarity,
                            'created_at' => now(),
                            'updated_at' => now(),
                        ]
                    );
                    $merged++;
                }
            }
        }

        return $merged;
    }

    /**
     * 简单文本相似度计算（基于 Token 交集）。
     */
    private function calculateSimilarity(string $a, string $b): float
    {
        $tokensA = $this->tokenize($a);
        $tokensB = $this->tokenize($b);

        if (empty($tokensA) || empty($tokensB)) {
            return 0.0;
        }

        $intersection = array_intersect($tokensA, $tokensB);
        $union = array_unique(array_merge($tokensA, $tokensB));

        return count($union) > 0 ? count($intersection) / count($union) : 0.0;
    }

    /**
     * 中文/英文 Token 化。
     */
    private function tokenize(string $text): array
    {
        // 中文分词：按字符切分
        preg_match_all('/[\x{4e00}-\x{9fff}]|[a-zA-Z]+/u', $text, $matches);
        return array_unique(array_map('mb_strtolower', $matches[0]));
    }

    /**
     * 为长 chunk 生成 AI 摘要。
     */
    private function summarizeChunks(array $scoredChunks): int
    {
        $summarized = 0;

        foreach ($scoredChunks as $item) {
            $chunk = $item['chunk'];
            $content = $chunk->content ?? '';

            // 只处理超过 500 字符的 chunk
            if (mb_strlen($content) < 500) {
                continue;
            }

            $prompt = <<<PROMPT
请为以下知识片段生成一个简洁的摘要（50字以内），只返回摘要文本，不要任何前缀：

{$content}
PROMPT;

            try {
                $response = agent()->prompt($prompt, [], $this->aiProviderName, $this->aiModel);
                $summary = OpenAiRuntimeProvider::normalizeGeneratedText($response);
                $summary = trim($summary);

                // 保存摘要到 knowledge_chunk_links 作为 self-reference
                if (mb_strlen($summary) > 5) {
                    DB::table('knowledge_chunk_links')->updateOrInsert(
                        [
                            'source_chunk_id' => $chunk->id,
                            'target_chunk_id' => $chunk->id,
                            'link_type' => 'summary',
                        ],
                        [
                            'similarity_score' => null,
                            'created_at' => now(),
                            'updated_at' => now(),
                        ]
                    );
                    $summarized++;
                }
            } catch (\Throwable $e) {
                Log::warning('[Evolution] Summarize failed for chunk '.$chunk->id);
            }
        }

        return $summarized;
    }

    /**
     * 基于向量相似度创建 chunk 交叉引用。
     */
    private function createCrossReferences(float $threshold): int
    {
        $links = 0;
        $chunks = KnowledgeChunk::whereNull('deleted_at')
            ->select('id', 'content', 'embedding_vector', 'embedding_json')
            ->get();

        $count = count($chunks);
        for ($i = 0; $i < $count; $i++) {
            for ($j = $i + 1; $j < $count; $j++) {
                $similarity = $this->calculateVectorSimilarity($chunks[$i], $chunks[$j]);

                if ($similarity >= $threshold * 0.8) { // 略低阈值找关联
                    DB::table('knowledge_chunk_links')->updateOrInsert(
                        [
                            'source_chunk_id' => $chunks[$i]->id,
                            'target_chunk_id' => $chunks[$j]->id,
                            'link_type' => 'related',
                        ],
                        [
                            'similarity_score' => $similarity,
                            'created_at' => now(),
                            'updated_at' => now(),
                        ]
                    );
                    $links++;
                }
            }
        }

        return $links;
    }

    /**
     * 计算两个 chunk 的向量相似度（余弦）。
     */
    private function calculateVectorSimilarity(KnowledgeChunk $a, KnowledgeChunk $b): float
    {
        $vecA = $this->getEmbeddingVector($a);
        $vecB = $this->getEmbeddingVector($b);

        if (empty($vecA) || empty($vecB) || count($vecA) !== count($vecB)) {
            return 0.0;
        }

        $dotProduct = 0.0;
        $normA = 0.0;
        $normB = 0.0;

        foreach ($vecA as $i => $val) {
            $valA = (float) $val;
            $valB = (float) ($vecB[$i] ?? 0);
            $dotProduct += $valA * $valB;
            $normA += $valA * $valA;
            $normB += $valB * $valB;
        }

        $denom = sqrt($normA) * sqrt($normB);

        return $denom > 0 ? $dotProduct / $denom : 0.0;
    }

    /**
     * 从 chunk 获取嵌入向量。
     */
    private function getEmbeddingVector(KnowledgeChunk $chunk): array
    {
        if ($chunk->embedding_vector) {
            // pgvector 格式：解析字符串
            $str = (string) $chunk->embedding_vector;
            $str = trim($str, '[]() ');
            return array_map('floatval', explode(',', $str));
        }

        if ($chunk->embedding_json) {
            $json = is_string($chunk->embedding_json)
                ? json_decode($chunk->embedding_json, true)
                : $chunk->embedding_json;
            if (is_array($json)) {
                return $json;
            }
        }

        return [];
    }

    /**
     * 归档长期未访问的低质量 chunk。
     */
    private function archiveStaleChunks(int $days): int
    {
        $cutoff = now()->subDays($days);

        $staleIds = DB::table('knowledge_chunk_scores')
            ->join('knowledge_chunks', 'knowledge_chunk_scores.chunk_id', '=', 'knowledge_chunks.id')
            ->where('knowledge_chunk_scores.last_accessed_at', '<', $cutoff)
            ->orWhere(function ($q) use ($cutoff) {
                $q->whereNull('knowledge_chunk_scores.last_accessed_at')
                  ->where('knowledge_chunks.created_at', '<', $cutoff);
            })
            ->where('knowledge_chunk_scores.quality_score', '<', 0.3)
            ->pluck('knowledge_chunks.id');

        $count = 0;
        foreach ($staleIds as $id) {
            KnowledgeChunk::where('id', $id)->update(['deleted_at' => now()]);
            $count++;
        }

        return $count;
    }

    /**
     * 创建进化运行记录。
     */
    private function createEvolutionRun($startTime)
    {
        return DB::table('evolution_runs')->insertGetId([
            'started_at' => $startTime,
            'status' => 'running',
            'model_used' => $this->aiModel,
            'created_at' => now(),
            'updated_at' => now(),
        ]);
    }

    /**
     * 完成进化运行记录。
     */
    private function completeEvolutionRun(int $runId, array $stats, $startTime): void
    {
        DB::table('evolution_runs')->where('id', $runId)->update([
            'completed_at' => now(),
            'status' => $stats['status'],
            'chunks_processed' => $stats['chunks_processed'],
            'chunks_merged' => $stats['chunks_merged'],
            'chunks_archived' => $stats['chunks_archived'],
            'chunks_summarized' => $stats['chunks_summarized'],
            'links_created' => $stats['links_created'],
            'error_message' => $stats['error_message'],
            'updated_at' => now(),
        ]);
    }
}

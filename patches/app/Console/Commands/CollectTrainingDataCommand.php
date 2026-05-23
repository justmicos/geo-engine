<?php

namespace App\Console\Commands;

use App\Models\KnowledgeChunk;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;

/**
 * v2.1: Artisan 命令 — 将知识库内容收集为微调训练数据集。
 *
 * 输出 JSONL 格式（Alpaca/ShareGPT 兼容），供 fine-tune/ 容器使用。
 *
 * 用法:
 *   php artisan geoflow:collect-training-data
 *   php artisan geoflow:collect-training-data --format=sharegpt --limit=500
 */
class CollectTrainingDataCommand extends Command
{
    protected $signature = 'geoflow:collect-training-data
                           {--format=alpaca : 输出格式: alpaca|sharegpt}
                           {--limit=1000 : 最大样本数}
                           {--min-score=0.7 : 最低质量分数}
                           {--output= : 输出路径（默认 fine-tune/datasets/training.jsonl）}';

    protected $description = 'Collect knowledge base content as fine-tuning dataset';

    public function handle(): int
    {
        $format = $this->option('format');
        $limit = (int) $this->option('limit');
        $minScore = (float) $this->option('min-score');
        $outputPath = $this->option('output') ?: base_path('../fine-tune/datasets/training.jsonl');

        $this->info("Collecting training data (format={$format}, limit={$limit}, min-score={$minScore})...");

        // 获取高分知识 chunk
        $chunksQuery = KnowledgeChunk::whereNull('deleted_at');

        // 如果存在质量分数表，按质量排序
        if (DB::getSchemaBuilder()->hasTable('knowledge_chunk_scores')) {
            $chunksQuery = $chunksQuery
                ->leftJoin('knowledge_chunk_scores', 'knowledge_chunks.id', '=', 'knowledge_chunk_scores.chunk_id')
                ->where(function ($q) use ($minScore) {
                    $q->whereNull('knowledge_chunk_scores.quality_score')
                      ->orWhere('knowledge_chunk_scores.quality_score', '>=', $minScore);
                })
                ->orderByDesc('knowledge_chunk_scores.quality_score');
        }

        $chunks = $chunksQuery->select('knowledge_chunks.*')->limit($limit)->get();

        if ($chunks->isEmpty()) {
            $this->warn('No knowledge chunks found.');
            return Command::FAILURE;
        }

        $samples = [];
        foreach ($chunks as $chunk) {
            $content = $chunk->content ?? '';
            if (mb_strlen($content) < 20) continue;

            $sample = $this->formatSample($content, $format);
            if ($sample !== null) {
                $samples[] = $sample;
            }
        }

        // 确保输出目录存在
        File::ensureDirectoryExists(dirname($outputPath));

        // 写入 JSONL
        $written = 0;
        $handle = fopen($outputPath, 'w');
        foreach ($samples as $sample) {
            fwrite($handle, json_encode($sample, JSON_UNESCAPED_UNICODE) . "\n");
            $written++;
        }
        fclose($handle);

        $this->info("Training data saved: {$outputPath} ({$written} samples)");

        return Command::SUCCESS;
    }

    /**
     * 将 chunk 内容格式化为指定格式。
     */
    private function formatSample(string $content, string $format): ?array
    {
        // 简单截断以避免过大样本
        $text = mb_substr($content, 0, 2048);

        return match ($format) {
            'sharegpt' => [
                'conversations' => [
                    ['from' => 'human', 'value' => "请介绍以下知识内容：" . mb_substr($text, 0, 200)],
                    ['from' => 'gpt', 'value' => $text],
                ],
            ],
            default => [
                'instruction' => "请基于知识库内容回答用户问题。",
                'input' => mb_substr($text, 0, 200),
                'output' => $text,
            ],
        };
    }
}

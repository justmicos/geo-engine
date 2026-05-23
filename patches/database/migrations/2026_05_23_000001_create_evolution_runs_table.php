<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * v2.1: 知识库进化运行记录表。
     *
     * 记录每次进化任务的时间、处理统计、状态等信息，
     * 用于监控进化效果和排查问题。
     */
    public function up(): void
    {
        Schema::create('evolution_runs', function (Blueprint $table) {
            $table->id();
            $table->timestamp('started_at')->nullable();
            $table->timestamp('completed_at')->nullable();
            $table->string('status', 20)->default('pending'); // pending|running|completed|failed
            $table->string('model_used', 100)->nullable();
            $table->integer('chunks_processed')->default(0);
            $table->integer('chunks_merged')->default(0);
            $table->integer('chunks_archived')->default(0);
            $table->integer('chunks_summarized')->default(0);
            $table->integer('links_created')->default(0);
            $table->text('error_message')->nullable();
            $table->json('details')->nullable();
            $table->timestamps();
        });

        // 知识块之间的关联表（进化自动生成的交叉引用）
        Schema::create('knowledge_chunk_links', function (Blueprint $table) {
            $table->id();
            $table->foreignId('source_chunk_id')->constrained('knowledge_chunks')->onDelete('cascade');
            $table->foreignId('target_chunk_id')->constrained('knowledge_chunks')->onDelete('cascade');
            $table->string('link_type', 50)->default('related'); // related|summary|reference|duplicate
            $table->float('similarity_score')->nullable();
            $table->timestamps();

            $table->unique(['source_chunk_id', 'target_chunk_id', 'link_type']);
        });

        // 知识块质量评分
        Schema::create('knowledge_chunk_scores', function (Blueprint $table) {
            $table->id();
            $table->foreignId('chunk_id')->constrained('knowledge_chunks')->onDelete('cascade');
            $table->float('quality_score')->nullable();       // 0-1, AI 评估质量
            $table->float('relevance_score')->nullable();     // 0-1, 关联性
            $table->float('freshness_score')->nullable();     // 0-1, 时效性
            $table->timestamp('last_accessed_at')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('knowledge_chunk_scores');
        Schema::dropIfExists('knowledge_chunk_links');
        Schema::dropIfExists('evolution_runs');
    }
};

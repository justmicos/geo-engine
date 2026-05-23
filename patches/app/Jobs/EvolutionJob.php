<?php

namespace App\Jobs;

use App\Services\GeoFlow\KnowledgeEvolutionService;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;

/**
 * v2.1: 知识库进化任务。
 *
 * 由调度器按 EVOLUTION_INTERVAL_HOURS 定时触发。
 * 也支持手动触发：php artisan geoflow:evolve --force
 */
class EvolutionJob implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public $timeout = 600; // 进化任务可能需要更长时间
    public $tries = 1;     // 不自动重试（由调度器负责下次触发）

    private bool $force;

    /**
     * 创建任务实例。
     */
    public function __construct(bool $force = false)
    {
        $this->force = $force;
    }

    /**
     * 执行进化任务。
     */
    public function handle(KnowledgeEvolutionService $service): void
    {
        if (!$this->force && !config('geoflow.evolution_enabled', true)) {
            Log::info('[Evolution] Disabled by config');
            return;
        }

        Log::info('[Evolution] Job started');

        $stats = $service->evolve();

        Log::info('[Evolution] Job completed', $stats);
    }
}

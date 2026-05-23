<?php

namespace App\Console\Commands;

use App\Jobs\EvolutionJob;
use Illuminate\Console\Command;

/**
 * v2.1: Artisan 命令 — 手动触发知识库进化。
 *
 * 用法:
 *   php artisan geoflow:evolve           # 仅当 evolution_enabled 时执行
 *   php artisan geoflow:evolve --force   # 强制执行
 */
class EvolutionCommand extends Command
{
    protected $signature = 'geoflow:evolve
                           {--force : 强制运行，忽略 evolution_enabled 配置}';

    protected $description = 'Trigger knowledge base evolution';

    public function handle(): int
    {
        $force = (bool) $this->option('force');

        if (!$force && !config('geoflow.evolution_enabled', true)) {
            $this->warn('Knowledge evolution is disabled (EVOLUTION_ENABLED=false). Use --force to override.');
            return Command::FAILURE;
        }

        $this->info('Dispatching evolution job...');
        EvolutionJob::dispatch($force);
        $this->info('Evolution job dispatched. Check logs for progress.');

        return Command::SUCCESS;
    }
}

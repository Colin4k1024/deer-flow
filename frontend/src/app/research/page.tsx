"use client";

import { PlusIcon, ClockIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  listProjects,
  type ProjectSummary,
  STATUS_DISPLAY_NAMES,
  PHASE_DISPLAY_NAMES,
  type ResearchStatus,
  type ResearchPhase,
} from "@/core/api/research";

function StatusBadge({ status }: { status: ResearchStatus }) {
  const variants: Record<
    ResearchStatus,
    "default" | "destructive" | "secondary" | "outline"
  > = {
    pending: "secondary",
    in_progress: "default",
    completed: "default",
    failed: "destructive",
    cancelled: "secondary",
  };

  return (
    <Badge variant={variants[status]}>{STATUS_DISPLAY_NAMES[status]}</Badge>
  );
}

function PhaseProgress({
  phase,
  progress,
}: {
  phase: ResearchPhase | null;
  progress: number;
}) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">
          {phase ? PHASE_DISPLAY_NAMES[phase] : "等待开始"}
        </span>
        <span className="text-muted-foreground">{progress}%</span>
      </div>
      <Progress value={progress} className="h-2" />
    </div>
  );
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ResearchListPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadProjects();
  }, []);

  async function loadProjects() {
    try {
      setLoading(true);
      setError(null);
      const response = await listProjects();
      setProjects(response.projects);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/50 backdrop-blur">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="text-xl font-bold text-white">
            DeerFlow
          </Link>
          <nav className="flex items-center gap-4">
            <Link href="/research">
              <Button variant="ghost" className="text-white">
                研究团队
              </Button>
            </Link>
            <Link href="/workspace">
              <Button variant="ghost" className="text-white">
                工作区
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">我的研究</h1>
            <p className="text-muted-foreground mt-2">
              管理您的深度研究报告项目
            </p>
          </div>
          <Link href="/research/new">
            <Button className="gap-2">
              <PlusIcon className="h-4 w-4" />
              新建研究
            </Button>
          </Link>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center py-12">
            <div className="border-primary h-8 w-8 animate-spin rounded-full border-2 border-t-transparent" />
          </div>
        )}

        {/* Error State */}
        {error && (
          <Card className="border-red-500/50 bg-red-500/10">
            <CardContent className="py-8 text-center text-red-400">
              {error}
              <Button variant="outline" className="ml-4" onClick={loadProjects}>
                重试
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Empty State */}
        {!loading && !error && projects.length === 0 && (
          <Card className="border-white/10 bg-white/5">
            <CardContent className="py-12 text-center">
              <div className="mb-4 text-4xl">📚</div>
              <h3 className="mb-2 text-lg font-medium text-white">
                暂无研究项目
              </h3>
              <p className="text-muted-foreground mb-6">
                开始您的第一个深度研究课题
              </p>
              <Link href="/research/new">
                <Button className="gap-2">
                  <PlusIcon className="h-4 w-4" />
                  创建研究
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}

        {/* Project List */}
        {!loading && !error && projects.length > 0 && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <Link
                key={project.project_id}
                href={`/research/${project.project_id}`}
              >
                <Card className="border-white/10 bg-white/5 transition-colors hover:bg-white/10">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <CardTitle className="line-clamp-1 text-lg text-white">
                        {project.topic}
                      </CardTitle>
                      <StatusBadge status={project.status} />
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <PhaseProgress
                      phase={project.current_phase}
                      progress={project.progress}
                    />
                    <div className="text-muted-foreground flex items-center gap-2 text-sm">
                      <ClockIcon className="h-4 w-4" />
                      <span>{formatDate(project.created_at)}</span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

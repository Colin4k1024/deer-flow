"use client";

import {
  ArrowLeftIcon,
  FileTextIcon,
  Loader2Icon,
  XIcon,
  CheckCircleIcon,
  AlertCircleIcon,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState, useCallback } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  getProjectDetail,
  getProjectOutputs,
  cancelProject,
  type ProjectDetail,
  type PhaseOutput,
  STATUS_DISPLAY_NAMES,
  PHASE_DISPLAY_NAMES,
  type ResearchStatus,
  type ResearchPhase,
} from "@/core/api/research";

// 阶段列表
const PHASES: ResearchPhase[] = [
  "planning",
  "collecting",
  "analyzing",
  "writing",
  "reviewing",
  "completed",
];

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

function PhaseTimeline({
  currentPhase,
  progress,
}: {
  currentPhase: ResearchPhase | null;
  progress: number;
}) {
  const currentIndex = currentPhase ? PHASES.indexOf(currentPhase) : -1;

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {PHASES.map((phase, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = index === currentIndex;
          const isPending = index > currentIndex;

          return (
            <div key={phase} className="flex flex-1 flex-col items-center">
              <div
                className={`mb-2 flex h-8 w-8 items-center justify-center rounded-full border-2 ${
                  isCompleted
                    ? "border-green-500 bg-green-500 text-white"
                    : isCurrent
                      ? "border-primary bg-primary text-primary-foreground"
                      : "text-muted-foreground border-white/20 bg-white/5"
                }`}
              >
                {isCompleted ? (
                  <CheckCircleIcon className="h-5 w-5" />
                ) : isCurrent ? (
                  <Loader2Icon className="h-4 w-4 animate-spin" />
                ) : (
                  <span className="text-sm">{index + 1}</span>
                )}
              </div>
              <span
                className={`text-xs ${
                  isPending ? "text-muted-foreground" : "text-white"
                }`}
              >
                {PHASE_DISPLAY_NAMES[phase]}
              </span>
            </div>
          );
        })}
      </div>
      <Progress value={progress} className="mt-4 h-2" />
    </div>
  );
}

function OutputCard({ output }: { output: PhaseOutput }) {
  return (
    <Card className="border-white/10 bg-white/5">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm text-white">
            {PHASE_DISPLAY_NAMES[output.phase]}
            {output.direction && ` - ${output.direction}`}
          </CardTitle>
          <span className="text-muted-foreground text-xs">
            {new Date(output.created_at).toLocaleString("zh-CN")}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="max-h-96 overflow-y-auto rounded-lg bg-black/20 p-4">
          <pre className="text-muted-foreground text-sm whitespace-pre-wrap">
            {output.content}
          </pre>
        </div>
      </CardContent>
    </Card>
  );
}

export default function ResearchDetailPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [outputs, setOutputs] = useState<PhaseOutput[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [projectData, outputsData] = await Promise.all([
        getProjectDetail(projectId),
        getProjectOutputs(projectId),
      ]);
      setProject(projectData);
      setOutputs(outputsData.outputs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void loadData();

    // 轮询进度（如果项目还在进行中）
    const interval = setInterval(() => {
      if (project && ["pending", "in_progress"].includes(project.status)) {
        void loadData();
      }
    }, 30000); // 30秒刷新一次

    return () => clearInterval(interval);
  }, [loadData, project?.status]);

  async function handleCancel() {
    if (!confirm("确定要取消这个研究项目吗？")) return;

    try {
      setCancelling(true);
      await cancelProject(projectId);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "取消失败");
    } finally {
      setCancelling(false);
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0a0a0a]">
        <Loader2Icon className="text-primary h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-[#0a0a0a]">
        <header className="border-b border-white/10 bg-black/50 backdrop-blur">
          <div className="container mx-auto flex h-16 items-center gap-4 px-4">
            <Link href="/research" className="text-white">
              <ArrowLeftIcon className="h-5 w-5" />
            </Link>
            <span className="text-lg font-medium text-white">研究详情</span>
          </div>
        </header>
        <div className="container mx-auto px-4 py-8">
          <Card className="border-red-500/50 bg-red-500/10">
            <CardContent className="py-8 text-center text-red-400">
              {error ?? "项目不存在"}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const isCompleted = project.status === "completed";
  const isFailed = project.status === "failed";
  const canCancel = ["pending", "in_progress"].includes(project.status);

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/50 backdrop-blur">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <Link href="/research" className="text-white">
              <ArrowLeftIcon className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-lg font-medium text-white">
                {project.topic}
              </h1>
              <p className="text-muted-foreground text-sm">
                项目ID: {project.project_id}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={project.status} />
            {canCancel && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleCancel}
                disabled={cancelling}
                className="border-red-500/50 text-red-400 hover:bg-red-500/10"
              >
                {cancelling ? (
                  <Loader2Icon className="h-4 w-4 animate-spin" />
                ) : (
                  <XIcon className="h-4 w-4" />
                )}
                取消
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Phase Timeline */}
        {!isFailed && (
          <PhaseTimeline
            currentPhase={project.current_phase}
            progress={project.progress}
          />
        )}

        {/* Error Message */}
        {project.error_message && (
          <Card className="mb-8 border-red-500/50 bg-red-500/10">
            <CardContent className="flex items-center gap-2 py-4">
              <AlertCircleIcon className="h-5 w-5 text-red-400" />
              <span className="text-red-400">{project.error_message}</span>
            </CardContent>
          </Card>
        )}

        {/* Tabs */}
        <Tabs defaultValue="outputs" className="space-y-4">
          <TabsList>
            <TabsTrigger value="outputs" className="gap-2">
              <FileTextIcon className="h-4 w-4" />
              中间产出
            </TabsTrigger>
            {isCompleted && (
              <TabsTrigger value="report" asChild>
                <Link href={`/research/${projectId}/report`}>最终报告</Link>
              </TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="outputs" className="space-y-4">
            {outputs.length === 0 ? (
              <Card className="border-white/10 bg-white/5">
                <CardContent className="text-muted-foreground py-8 text-center">
                  暂无中间产出，研究可能还在进行中...
                </CardContent>
              </Card>
            ) : (
              outputs.map((output, index) => (
                <OutputCard key={index} output={output} />
              ))
            )}
          </TabsContent>

          {isCompleted && (
            <TabsContent value="report">
              <Card className="border-white/10 bg-white/5">
                <CardContent className="py-8 text-center">
                  <p className="text-muted-foreground mb-4">报告已生成完毕</p>
                  <Link href={`/research/${projectId}/report`}>
                    <Button>查看完整报告</Button>
                  </Link>
                </CardContent>
              </Card>
            </TabsContent>
          )}
        </Tabs>

        {/* Project Info */}
        <Card className="mt-8 border-white/10 bg-white/5">
          <CardHeader>
            <CardTitle className="text-white">项目信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">研究方向</span>
              <span className="text-white">
                {project.directions.join(", ")}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">创建时间</span>
              <span className="text-white">
                {new Date(project.created_at).toLocaleString("zh-CN")}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">更新时间</span>
              <span className="text-white">
                {new Date(project.updated_at).toLocaleString("zh-CN")}
              </span>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

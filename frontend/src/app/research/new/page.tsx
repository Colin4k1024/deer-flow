"use client";

import { ArrowLeftIcon, Loader2Icon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createProject } from "@/core/api/research";

const DEFAULT_DIRECTIONS = [
  "技术趋势",
  "市场分析",
  "应用案例",
  "竞争格局",
  "政策环境",
];

export default function NewResearchPage() {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const [directions, setDirections] = useState<string[]>(DEFAULT_DIRECTIONS);
  const [customDirection, setCustomDirection] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!topic.trim()) {
      setError("请输入研究课题");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const selectedDirections = directions.filter((d) => d.trim());
      const response = await createProject({
        topic: topic.trim(),
        directions: selectedDirections,
      });

      // 跳转到项目详情页
      router.push(`/research/${response.project_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setLoading(false);
    }
  }

  function toggleDirection(direction: string) {
    setDirections((prev) =>
      prev.includes(direction)
        ? prev.filter((d) => d !== direction)
        : [...prev, direction],
    );
  }

  function addCustomDirection() {
    if (
      customDirection.trim() &&
      !directions.includes(customDirection.trim())
    ) {
      setDirections((prev) => [...prev, customDirection.trim()]);
      setCustomDirection("");
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/50 backdrop-blur">
        <div className="container mx-auto flex h-16 items-center gap-4 px-4">
          <Link href="/research" className="text-white">
            <ArrowLeftIcon className="h-5 w-5" />
          </Link>
          <span className="text-lg font-medium text-white">新建研究</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto max-w-2xl px-4 py-8">
        <Card className="border-white/10 bg-white/5">
          <CardHeader>
            <CardTitle className="text-white">创建研究项目</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Topic Input */}
              <div className="space-y-2">
                <label htmlFor="topic" className="text-white">
                  研究课题 <span className="text-red-400">*</span>
                </label>
                <Input
                  id="topic"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="例如：2026年协作机器人发展趋势"
                  className="placeholder:text-muted-foreground bg-white/10 text-white"
                  disabled={loading}
                />
                <p className="text-muted-foreground text-sm">
                  描述您想要研究的主题，越具体越好
                </p>
              </div>

              {/* Direction Selection */}
              <div className="space-y-3">
                <label className="text-white">研究方向</label>
                <div className="flex flex-wrap gap-2">
                  {DEFAULT_DIRECTIONS.map((direction) => (
                    <Button
                      key={direction}
                      type="button"
                      variant={
                        directions.includes(direction) ? "default" : "outline"
                      }
                      size="sm"
                      onClick={() => toggleDirection(direction)}
                      disabled={loading}
                      className={
                        directions.includes(direction)
                          ? "bg-primary text-primary-foreground"
                          : "border-white/20 text-white hover:bg-white/10"
                      }
                    >
                      {direction}
                    </Button>
                  ))}
                </div>

                {/* Custom Direction */}
                <div className="flex gap-2">
                  <Input
                    value={customDirection}
                    onChange={(e) => setCustomDirection(e.target.value)}
                    placeholder="添加自定义研究方向"
                    className="placeholder:text-muted-foreground bg-white/10 text-white"
                    disabled={loading}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addCustomDirection();
                      }
                    }}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={addCustomDirection}
                    disabled={loading || !customDirection.trim()}
                    className="border-white/20 text-white hover:bg-white/10"
                  >
                    添加
                  </Button>
                </div>

                {/* Selected Directions */}
                {directions.length > 0 && (
                  <div className="mt-2">
                    <p className="text-muted-foreground mb-2 text-sm">
                      已选择 {directions.length} 个方向：
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {directions.map((d) => (
                        <span
                          key={d}
                          className="bg-primary/20 text-primary inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm"
                        >
                          {d}
                          <button
                            type="button"
                            onClick={() => toggleDirection(d)}
                            className="hover:text-primary-foreground ml-1"
                            disabled={loading}
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Error Message */}
              {error && (
                <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400">
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <div className="flex gap-4">
                <Button
                  type="submit"
                  disabled={loading || !topic.trim()}
                  className="flex-1"
                >
                  {loading ? (
                    <>
                      <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                      创建中...
                    </>
                  ) : (
                    "开始研究"
                  )}
                </Button>
                <Link href="/research">
                  <Button
                    type="button"
                    variant="outline"
                    disabled={loading}
                    className="border-white/20 text-white hover:bg-white/10"
                  >
                    取消
                  </Button>
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Tips */}
        <div className="mt-8 rounded-lg border border-white/10 bg-white/5 p-4">
          <h3 className="mb-2 font-medium text-white">💡 研究小贴士</h3>
          <ul className="text-muted-foreground space-y-1 text-sm">
            <li>• 研究课题越具体，报告质量越高</li>
            <li>• 选择多个研究方向可获得更全面的分析</li>
            <li>• 研究可能需要 10-30 分钟完成，请耐心等待</li>
            <li>• 您可以随时返回查看研究进度</li>
          </ul>
        </div>
      </main>
    </div>
  );
}

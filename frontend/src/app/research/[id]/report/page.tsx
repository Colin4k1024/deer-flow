"use client";

import {
  ArrowLeftIcon,
  CopyIcon,
  DownloadIcon,
  Loader2Icon,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import * as React from "react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getProjectReport, type ReportResponse } from "@/core/api/research";

function ReportContent({ report }: { report: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  }

  function handleDownload() {
    const blob = new Blob([report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "research_report.md";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return (
    <>
      {/* Actions */}
      <div className="mb-6 flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopy}
          className="border-white/20 text-white hover:bg-white/10"
        >
          <CopyIcon className="mr-2 h-4 w-4" />
          {copied ? "已复制" : "复制"}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleDownload}
          className="border-white/20 text-white hover:bg-white/10"
        >
          <DownloadIcon className="mr-2 h-4 w-4" />
          下载
        </Button>
      </div>

      {/* Report Content */}
      <Card className="border-white/10 bg-white/5">
        <CardContent className="p-8">
          <div
            className="prose prose-invert max-w-none"
            style={{
              color: "rgb(161 161 169)", // muted-foreground
            }}
          >
            {/* 简单的 Markdown 渲染 */}
            <ReportMarkdown content={report} />
          </div>
        </CardContent>
      </Card>
    </>
  );
}

/**
 * 简单的 Markdown 渲染组件
 * 处理标题、段落、列表、粗体、链接等
 */
function ReportMarkdown({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.JSX.Element[] = [];
  let listItems: string[] = [];

  function flushList() {
    if (listItems.length > 0) {
      elements.push(
        <ul key={elements.length} className="my-4 list-disc space-y-2 pl-6">
          {listItems.map((item, i) => (
            <li key={i}>{renderInline(item)}</li>
          ))}
        </ul>,
      );
      listItems = [];
    }
  }

  function renderInline(text: string): React.JSX.Element {
    // 处理粗体
    const boldRegex = /\*\*(.+?)\*\*/g;
    const parts: (string | React.JSX.Element)[] = [];
    let lastIndex = 0;
    let match;

    while ((match = boldRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }
      parts.push(<strong key={match.index}>{match[1]}</strong>);
      lastIndex = boldRegex.lastIndex;
    }
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return <>{parts.length > 0 ? parts : text}</>;
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line) continue;

    // 跳过空行
    if (!line.trim()) {
      flushList();
      continue;
    }

    // 标题
    if (line.startsWith("# ")) {
      flushList();
      elements.push(
        <h1
          key={i}
          className="mt-8 mb-6 text-3xl font-bold text-white first:mt-0"
        >
          {line.slice(2)}
        </h1>,
      );
      continue;
    }
    if (line.startsWith("## ")) {
      flushList();
      elements.push(
        <h2
          key={i}
          className="mt-8 mb-4 text-2xl font-bold text-white first:mt-0"
        >
          {line.slice(3)}
        </h2>,
      );
      continue;
    }
    if (line.startsWith("### ")) {
      flushList();
      elements.push(
        <h3 key={i} className="mt-6 mb-3 text-xl font-semibold text-white">
          {line.slice(4)}
        </h3>,
      );
      continue;
    }

    // 列表项
    if (/^[-*]\s/.exec(line)) {
      listItems.push(line.slice(2));
      continue;
    }
    if (/^\d+\.\s/.exec(line)) {
      listItems.push(line.replace(/^\d+\.\s/, ""));
      continue;
    }

    // 段落
    flushList();
    elements.push(
      <p key={i} className="my-4 leading-relaxed">
        {renderInline(line)}
      </p>,
    );
  }

  flushList();

  return <>{elements}</>;
}

export default function ReportPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [reportData, setReportData] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadReport();
  }, [projectId]);

  async function loadReport() {
    try {
      setLoading(true);
      const data = await getProjectReport(projectId);
      setReportData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0a0a0a]">
        <Loader2Icon className="text-primary h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error || !reportData) {
    return (
      <div className="min-h-screen bg-[#0a0a0a]">
        <header className="border-b border-white/10 bg-black/50 backdrop-blur">
          <div className="container mx-auto flex h-16 items-center gap-4 px-4">
            <Link href={`/research/${projectId}`} className="text-white">
              <ArrowLeftIcon className="h-5 w-5" />
            </Link>
            <span className="text-lg font-medium text-white">研究报告</span>
          </div>
        </header>
        <div className="container mx-auto px-4 py-8">
          <Card className="border-red-500/50 bg-red-500/10">
            <CardContent className="py-8 text-center text-red-400">
              {error ?? "报告不存在"}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!reportData.report) {
    return (
      <div className="min-h-screen bg-[#0a0a0a]">
        <header className="border-b border-white/10 bg-black/50 backdrop-blur">
          <div className="container mx-auto flex h-16 items-center gap-4 px-4">
            <Link href={`/research/${projectId}`} className="text-white">
              <ArrowLeftIcon className="h-5 w-5" />
            </Link>
            <span className="text-lg font-medium text-white">研究报告</span>
          </div>
        </header>
        <div className="container mx-auto px-4 py-8">
          <Card className="border-white/10 bg-white/5">
            <CardContent className="text-muted-foreground py-8 text-center">
              {reportData.message ?? "报告暂不可用"}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-white/10 bg-black/80 backdrop-blur">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <Link href={`/research/${projectId}`} className="text-white">
              <ArrowLeftIcon className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-lg font-medium text-white">研究报告</h1>
              <p className="text-muted-foreground text-sm">
                {reportData.word_count?.toLocaleString()} 字
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto max-w-4xl px-4 py-8">
        <ReportContent report={reportData.report} />
      </main>
    </div>
  );
}

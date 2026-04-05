"use client";

import { getBackendBaseURL } from "../config";

/**
 * Research API Client
 *
 * 后端研究团队协作系统的 API 客户端
 */

export interface CreateProjectRequest {
  topic: string;
  directions: string[];
}

export interface CreateProjectResponse {
  project_id: string;
  status: ResearchStatus;
  created_at: string;
  message: string;
}

export type ResearchStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "failed"
  | "cancelled";

export type ResearchPhase =
  | "planning"
  | "collecting"
  | "analyzing"
  | "writing"
  | "reviewing"
  | "completed";

export interface ProjectSummary {
  project_id: string;
  topic: string;
  status: ResearchStatus;
  progress: number;
  current_phase: ResearchPhase | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  projects: ProjectSummary[];
  total: number;
}

export interface ProjectDetail {
  project_id: string;
  topic: string;
  directions: string[];
  status: ResearchStatus;
  progress: number;
  current_phase: ResearchPhase | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface PhaseOutput {
  phase: ResearchPhase;
  direction: string | null;
  content: string;
  created_at: string;
}

export interface PhaseOutputsResponse {
  project_id: string;
  outputs: PhaseOutput[];
}

export interface ReportResponse {
  project_id: string;
  report: string | null;
  format: string;
  word_count: number | null;
  message: string | null;
}

export interface CancelProjectResponse {
  project_id: string;
  status: ResearchStatus;
  message: string;
}

// 获取用户 ID（从 localStorage 或模拟）
function getUserId(): string {
  if (typeof window === "undefined") return "anonymous";
  return localStorage.getItem("research_user_id") ?? "anonymous";
}

// 获取请求头
function getHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-User-ID": getUserId(),
  };
}

// 获取后端基础 URL
function getResearchBaseURL(): string {
  if (typeof window === "undefined") return "";
  return getBackendBaseURL() || "/api";
}

/**
 * 创建研究项目
 */
export async function createProject(
  data: CreateProjectRequest,
): Promise<CreateProjectResponse> {
  const url = `${getResearchBaseURL()}/research/projects`;
  const response = await fetch(url, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * 获取用户的研究项目列表
 */
export async function listProjects(): Promise<ProjectListResponse> {
  const url = `${getResearchBaseURL()}/research/projects`;
  const response = await fetch(url, {
    method: "GET",
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * 获取研究项目详情
 */
export async function getProjectDetail(
  projectId: string,
): Promise<ProjectDetail> {
  const url = `${getResearchBaseURL()}/research/projects/${projectId}`;
  const response = await fetch(url, {
    method: "GET",
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * 获取研究项目中间产出
 */
export async function getProjectOutputs(
  projectId: string,
): Promise<PhaseOutputsResponse> {
  const url = `${getResearchBaseURL()}/research/projects/${projectId}/outputs`;
  const response = await fetch(url, {
    method: "GET",
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * 获取研究项目最终报告
 */
export async function getProjectReport(
  projectId: string,
): Promise<ReportResponse> {
  const url = `${getResearchBaseURL()}/research/projects/${projectId}/report`;
  const response = await fetch(url, {
    method: "GET",
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * 取消研究项目
 */
export async function cancelProject(
  projectId: string,
): Promise<CancelProjectResponse> {
  const url = `${getResearchBaseURL()}/research/projects/${projectId}`;
  const response = await fetch(url, {
    method: "DELETE",
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * 阶段显示名称映射
 */
export const PHASE_DISPLAY_NAMES: Record<ResearchPhase, string> = {
  planning: "制定计划",
  collecting: "信息搜集",
  analyzing: "分析",
  writing: "报告撰写",
  reviewing: "审核中",
  completed: "已完成",
};

/**
 * 状态显示名称映射
 */
export const STATUS_DISPLAY_NAMES: Record<ResearchStatus, string> = {
  pending: "待处理",
  in_progress: "进行中",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
};

import { ArrowUpTrayIcon } from "@heroicons/react/24/outline";
import React, { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import useSWR from "swr";
import Sidebar from "../components/Sidebar";
import { FolderNode } from "../components/VideoTree";
import { useApi } from "../hooks/useApi";

const flattenFolders = (nodes: FolderNode[], prefix = ""): { id: number; label: string }[] => {
  return nodes.flatMap((node) => {
    const currentLabel = `${prefix}/${node.name}`;
    return [
      { id: node.id, label: currentLabel },
      ...flattenFolders(node.children ?? [], currentLabel)
    ];
  });
};

const UploadPage: React.FC = () => {
  const api = useApi();
  const navigate = useNavigate();
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [jsonFile, setJsonFile] = useState<File | null>(null);
  const [folderId, setFolderId] = useState<number | "">("");
  const [duration, setDuration] = useState<string>("");
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { data: folders } = useSWR<FolderNode[]>("/folders/tree", (url) => api.get(url).then((res) => res.data));
  const folderOptions = useMemo(() => flattenFolders(folders ?? []), [folders]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!videoFile || !jsonFile) {
      setStatus("请同时选择视频文件 (.mp4) 与转录 JSON 文件");
      return;
    }
    setLoading(true);
    setStatus(null);

    try {
      const formData = new FormData();
      formData.append("video_file", videoFile);
      formData.append("transcript_file", jsonFile);
      if (folderId !== "") {
        formData.append("folder_id", String(folderId));
      }
      if (duration) {
        formData.append("duration", duration);
      }
      await api.post("/videos/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setStatus("上传成功，正在跳转视频库...");
      setTimeout(() => navigate("/library"), 1000);
    } catch (error) {
      console.error(error);
      setStatus("上传失败，请检查文件格式或稍后再试");
    } finally {
      setLoading(false);
    }
  };

  const validateVideo = (file: File | null) => {
    if (file && !file.name.endsWith(".mp4")) {
      setStatus("视频文件必须是 .mp4 格式");
      setVideoFile(null);
    } else {
      setStatus(null);
      setVideoFile(file);
    }
  };

  const validateJson = (file: File | null) => {
    if (file && !file.name.endsWith(".json")) {
      setStatus("转录文件必须是 .json 格式");
      setJsonFile(null);
    } else {
      setStatus(null);
      setJsonFile(file);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar />
      <main className="flex-1 px-6 py-6">
        <form
          onSubmit={handleSubmit}
          className="mx-auto max-w-3xl space-y-6 rounded-xl border border-slate-800 bg-slate-900/70 p-8"
        >
          <header className="flex items-center gap-3">
            <div className="rounded-full bg-primary/20 p-2 text-primary">
              <ArrowUpTrayIcon className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">上传培训资料</h1>
              <p className="text-sm text-slate-400">请选择 .mp4 视频与对应的转录 JSON 文件。</p>
            </div>
          </header>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm text-slate-300">选择目录</label>
              <select
                value={folderId}
                onChange={(event) => setFolderId(event.target.value === "" ? "" : Number(event.target.value))}
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-primary focus:outline-none"
              >
                <option value="">根目录</option>
                {folderOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">视频时长（秒，可选）</label>
              <input
                type="number"
                min="0"
                step="1"
                value={duration}
                onChange={(event) => setDuration(event.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-primary focus:outline-none"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm text-slate-300">视频文件 (.mp4)</label>
            <input
              type="file"
              accept="video/mp4"
              onChange={(event) => validateVideo(event.target.files?.[0] ?? null)}
              className="block w-full rounded-md border border-dashed border-slate-700 bg-slate-900 px-3 py-6 text-sm text-slate-400 focus:border-primary focus:outline-none"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm text-slate-300">转录 JSON 文件</label>
            <input
              type="file"
              accept="application/json"
              onChange={(event) => validateJson(event.target.files?.[0] ?? null)}
              className="block w-full rounded-md border border-dashed border-slate-700 bg-slate-900 px-3 py-6 text-sm text-slate-400 focus:border-primary focus:outline-none"
            />
          </div>

          {status && <div className="rounded-md border border-slate-700 bg-slate-900/60 px-4 py-2 text-sm text-slate-300">{status}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-white transition hover:bg-primary-dark disabled:bg-slate-700"
          >
            {loading ? "上传中..." : "上传"}
          </button>
        </form>
      </main>
    </div>
  );
};

export default UploadPage;

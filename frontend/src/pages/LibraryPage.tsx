import { ClockIcon } from "@heroicons/react/24/outline";
import dayjs from "dayjs";
import React, { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import useSWR from "swr";
import Sidebar from "../components/Sidebar";
import VideoTree, { FolderNode } from "../components/VideoTree";
import { useApi } from "../hooks/useApi";

interface VideoItem {
  id: number;
  filename: string;
  path: string;
  duration: number | null;
  created_at: string;
}

const LibraryPage: React.FC = () => {
  const api = useApi();
  const navigate = useNavigate();
  const [selectedFolder, setSelectedFolder] = useState<number | null>(null);

  const fetcher = useMemo(() => (url: string) => api.get(url).then((response) => response.data), [api]);

  const { data: folders } = useSWR<FolderNode[]>("/folders/tree", fetcher);
  const { data: videos } = useSWR<VideoItem[]>(
    ["/videos", selectedFolder],
    ([url, folder]) => api.get(url, { params: { folder_id: folder ?? undefined } }).then((response) => response.data)
  );

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar />
      <main className="flex-1 px-6 py-6">
        <div className="grid gap-6 md:grid-cols-[260px_1fr]">
          <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
            <h2 className="text-sm font-semibold text-slate-200">目录</h2>
            <div className="mt-3">
              <VideoTree
                folders={folders ?? []}
                selectedFolderId={selectedFolder}
                onSelect={setSelectedFolder}
              />
            </div>
          </section>
          <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-6">
            <header className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">培训视频</h2>
                <p className="text-sm text-slate-400">选择视频开始学习，学习进度将自动保存。</p>
              </div>
            </header>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {videos?.map((video) => (
                <button
                  key={video.id}
                  onClick={() => navigate(`/player/${video.id}`)}
                  className="group flex flex-col rounded-lg border border-slate-800 bg-slate-900/60 p-4 text-left transition hover:border-primary hover:bg-primary/20"
                >
                  <div className="flex items-center justify-between">
                    <span className="truncate text-sm font-semibold text-white" title={video.filename}>
                      {video.filename}
                    </span>
                    <ClockIcon className="h-4 w-4 text-slate-400" />
                  </div>
                  <p className="mt-2 line-clamp-2 text-xs text-slate-400">路径：{video.path}</p>
                  <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
                    <span>上传于 {dayjs(video.created_at).format("YYYY-MM-DD")}</span>
                    {video.duration && <span>时长 {(video.duration / 60).toFixed(1)} 分钟</span>}
                  </div>
                </button>
              ))}
              {videos && videos.length === 0 && (
                <div className="col-span-full rounded-lg border border-dashed border-slate-800 bg-slate-900/40 p-8 text-center text-sm text-slate-500">
                  当前目录暂无视频，快去上传吧！
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default LibraryPage;

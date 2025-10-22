import React, { useCallback, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import useSWR from "swr";
import AssistantPanel from "../components/AssistantPanel";
import Sidebar from "../components/Sidebar";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../hooks/useAuth";

interface VideoDetail {
  id: number;
  filename: string;
  path: string;
  duration: number | null;
  playback_url: string;
  transcript_url: string | null;
}

interface ProgressState {
  user_id: number;
  video_id: number;
  last_position: number;
  completed: boolean;
}

const PlayerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const videoId = Number(id);
  const api = useApi();
  const { token } = useAuth();
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const fetcher = (url: string) => api.get(url).then((res) => res.data);
  const { data: video } = useSWR<VideoDetail>(id ? `/videos/${id}` : null, fetcher);
  const { data: progress } = useSWR<ProgressState | null>(
    id ? `/progress/${id}` : null,
    fetcher
  );

  useEffect(() => {
    const element = videoRef.current;
    if (!element || !progress) {
      return;
    }
    if (progress.last_position) {
      element.currentTime = progress.last_position;
    }
  }, [progress]);

  const reportProgress = useCallback(async () => {
    const element = videoRef.current;
    if (!element || !video) {
      return;
    }
    const payload = {
      video_id: video.id,
      last_position: element.currentTime,
      duration: element.duration || video.duration || 0
    };
    try {
      await api.post("/progress", payload);
    } catch (error) {
      console.error("Failed to update progress", error);
    }
  }, [api, video]);

  useEffect(() => {
    const element = videoRef.current;
    if (!element) {
      return;
    }
    const handlePause = () => reportProgress();
    const handleEnded = () => reportProgress();
    element.addEventListener("pause", handlePause);
    element.addEventListener("ended", handleEnded);

    const interval = window.setInterval(() => {
      void reportProgress();
    }, 10000);

    return () => {
      element.removeEventListener("pause", handlePause);
      element.removeEventListener("ended", handleEnded);
      window.clearInterval(interval);
      void reportProgress();
    };
  }, [reportProgress]);

  if (!video) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-100">
        正在加载视频...
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar />
      <main className="flex flex-1 flex-col gap-4 px-6 py-6">
        <header className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          <h1 className="text-lg font-semibold text-white">{video.filename}</h1>
          <p className="text-sm text-slate-400">路径：{video.path}</p>
        </header>
        <div className="grid flex-1 gap-4 lg:grid-cols-[2fr_1fr]">
          <section className="relative rounded-xl border border-slate-800 bg-black">
            <video
              ref={videoRef}
              src={
                token
                  ? `${video.playback_url}?access_token=${encodeURIComponent(token)}`
                  : video.playback_url
              }
              controls
              className="h-full w-full rounded-xl"
            />
          </section>
          <section className="rounded-xl border border-slate-800 bg-slate-900/70">
            <AssistantPanel videoId={video.id} />
          </section>
        </div>
      </main>
    </div>
  );
};

export default PlayerPage;

import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import { videosAPI, progressAPI } from '../services/api';
import type { Video, LearningProgress } from '../types';
import Layout from '../components/Layout';
import MaterialsManager from '../components/MaterialsManager';
import { ChatPanel } from '../components/ChatPanel';
import { QuizModal } from '../components/QuizModal';
import { useAuth } from '../contexts/AuthContext';

const VideoPlayerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [video, setVideo] = useState<Video | null>(null);
  const [progress, setProgress] = useState<LearningProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [showQuiz, setShowQuiz] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const playerRef = useRef<any>(null);

  useEffect(() => {
    loadVideo();
    return () => {
      // Cleanup video player on unmount
      if (playerRef.current) {
        playerRef.current.dispose();
      }
    };
  }, [id]);

  const loadVideo = async () => {
    if (!id) return;

    try {
      const [videoData, progressData] = await Promise.all([
        videosAPI.get(parseInt(id)),
        progressAPI.getMyProgress(parseInt(id)).catch(() => []),
      ]);

      setVideo(videoData);
      setProgress(progressData[0] || null);
      setLoading(false);

      // Initialize video player after data is loaded
      setTimeout(() => initializePlayer(videoData, progressData[0]), 100);
    } catch (error) {
      console.error('Error loading video:', error);
      setLoading(false);
    }
  };

  const initializePlayer = (videoData: Video, progressData?: LearningProgress) => {
    if (!videoRef.current) return;

    // Check if player already exists to avoid duplicate initialization
    if (playerRef.current) {
      return;
    }

    const player = videojs(videoRef.current, {
      controls: true,
      responsive: true,
      fluid: true,
      preload: 'auto',
      sources: [
        {
          src: videoData.video_url,
          type: 'video/mp4',
        },
      ],
      tracks: [
        {
          kind: 'subtitles',
          src: videoData.transcript_url,
          srclang: 'en',
          label: 'English',
          default: true,
        },
      ],
    });

    playerRef.current = player;

    // Resume from last position
    if (progressData?.current_timestamp) {
      player.currentTime(progressData.current_timestamp);
    }

    // Track progress
    let lastUpdateTime = 0;
    player.on('timeupdate', () => {
      const currentTime = player.currentTime() || 0;
      const duration = player.duration() || 1;

      // Update current time state for ChatPanel
      setCurrentTime(currentTime);

      // Update progress every 5 seconds
      if (currentTime - lastUpdateTime >= 5 || player.ended()) {
        lastUpdateTime = currentTime;
        updateProgress(currentTime, duration);
      }
    });

    player.on('ended', () => {
      const duration = player.duration() || 1;
      updateProgress(duration, duration, true);
    });
  };

  const updateProgress = async (
    currentTime: number,
    duration: number,
    completed = false
  ) => {
    if (!id) return;

    const completionPercentage = (currentTime / duration) * 100;
    const isCompleted = completed || completionPercentage >= 95;

    try {
      const updatedProgress = await progressAPI.update({
        video_id: parseInt(id),
        current_timestamp: currentTime,
        completion_percentage: Math.min(completionPercentage, 100),
        is_completed: isCompleted,
      });

      setProgress(updatedProgress);
    } catch (error) {
      console.error('Error updating progress:', error);
    }
  };

  const handleTimestampClick = (timestamp: number) => {
    if (playerRef.current) {
      playerRef.current.currentTime(timestamp);
      playerRef.current.play();
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading video...</p>
        </div>
      </Layout>
    );
  }

  if (!video) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-red-600">Video not found</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className={`${isChatOpen ? 'flex gap-4' : 'max-w-5xl mx-auto'} relative`}>
        {/* Main Content Area */}
        <div className={`${isChatOpen ? 'flex-1' : ''} space-y-6`}>
          {/* Chat Toggle Button */}
          <div className="flex justify-end mb-2">
            <button
              onClick={() => setIsChatOpen(!isChatOpen)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-md"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
              {isChatOpen ? 'Close AI Assistant' : 'Open AI Assistant'}
            </button>
          </div>

          {/* Video Player */}
          <div className="bg-black rounded-lg overflow-hidden">
            <div data-vjs-player>
              <video ref={videoRef} className="video-js vjs-big-play-centered" />
            </div>
          </div>

          {/* Video Info */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h1 className="text-2xl font-bold mb-2">{video.title}</h1>
            {video.description && (
              <p className="text-gray-600 mb-4">{video.description}</p>
            )}

            {/* Progress Bar */}
            {progress && (
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Your Progress</span>
                  <span>{Math.round(progress.completion_percentage)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${progress.completion_percentage}%` }}
                  />
                </div>
                {progress.is_completed && (
                  <p className="text-green-600 text-sm mt-2">✓ Completed</p>
                )}
              </div>
            )}

            {video.tags && (
              <div className="flex flex-wrap gap-2 mb-4">
                {video.tags.split(',').map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                  >
                    {tag.trim()}
                  </span>
                ))}
              </div>
            )}

            {/* AI Assistant Status */}
            <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">AI Assistant Status:</span>
                {video.vectorization_status === 'completed' && (
                  <span className="px-3 py-1 text-sm font-medium rounded bg-green-100 text-green-800">
                    ✓ Ready
                  </span>
                )}
                {video.vectorization_status === 'processing' && (
                  <span className="px-3 py-1 text-sm font-medium rounded bg-blue-100 text-blue-800 animate-pulse">
                    Processing...
                  </span>
                )}
                {video.vectorization_status === 'pending' && (
                  <span className="px-3 py-1 text-sm font-medium rounded bg-yellow-100 text-yellow-800">
                    Pending
                  </span>
                )}
                {video.vectorization_status === 'failed' && (
                  <span className="px-3 py-1 text-sm font-medium rounded bg-red-100 text-red-800">
                    Failed
                  </span>
                )}
              </div>
              {video.vectorization_status === 'completed' && (
                <p className="text-xs text-gray-500 mt-1">
                  Chat and Voice features are available
                </p>
              )}
              {video.vectorization_status === 'processing' && (
                <p className="text-xs text-gray-500 mt-1">
                  AI features will be available shortly...
                </p>
              )}
              {video.vectorization_status === 'failed' && video.vectorization_error && (
                <p className="text-xs text-red-600 mt-1">
                  Error: {video.vectorization_error}
                </p>
              )}
            </div>

            <div className="text-sm text-gray-500">
              Uploaded on {new Date(video.created_at).toLocaleDateString()}
            </div>
          </div>

          {/* Training Materials - Admin can manage, users can view */}
          {user?.is_admin ? (
            <MaterialsManager
              videoId={parseInt(id!)}
              materials={video.materials || []}
              onMaterialAdded={loadVideo}
              onMaterialDeleted={loadVideo}
            />
          ) : (
            video.materials && video.materials.length > 0 && (
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-bold mb-4">📚 Training Materials</h2>
                <div className="space-y-3">
                  {video.materials.map((material) => (
                    <div
                      key={material.id}
                      className="flex items-start justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-2xl">
                            {getFileIcon(material.file_type || material.original_filename)}
                          </span>
                          <h3 className="font-semibold text-gray-900">
                            {material.title || material.original_filename}
                          </h3>
                        </div>
                        {material.description && (
                          <p className="text-sm text-gray-600 mb-2 ml-8">
                            {material.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 text-xs text-gray-500 ml-8">
                          <span>{formatFileSize(material.file_size)}</span>
                          <span>•</span>
                          <span>{getFileExtension(material.original_filename)}</span>
                        </div>
                      </div>
                      <a
                        href={material.file_url}
                        download={material.original_filename}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2 text-sm font-medium"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                          />
                        </svg>
                        Download
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )
          )}

          {/* AI-Generated Content (Phase 2) */}
          {(video.ai_summary || video.ai_outline || video.ai_key_terms) && (
            <div className="bg-white p-6 rounded-lg shadow space-y-6">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <h2 className="text-xl font-bold text-gray-900">AI-Generated Insights</h2>
              </div>

              {/* AI Summary */}
              {video.ai_summary && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Summary
                  </h3>
                  <p className="text-gray-700 leading-relaxed">{video.ai_summary}</p>
                </div>
              )}

              {/* AI Outline */}
              {video.ai_outline && (() => {
                try {
                  const outline = JSON.parse(video.ai_outline);
                  if (outline && outline.length > 0) {
                    return (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                          <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                          Content Outline
                        </h3>
                        <ul className="space-y-2">
                          {outline.map((item: any, idx: number) => (
                            <li key={idx} className="flex items-start">
                              <span className="inline-block w-6 h-6 bg-green-100 text-green-700 rounded-full text-center text-sm font-semibold mr-3 mt-0.5 flex-shrink-0">
                                {idx + 1}
                              </span>
                              <div className="flex-1">
                                <p className="text-gray-800">{item.topic || item}</p>
                                {item.timestamp && (
                                  <p className="text-sm text-gray-500 mt-1">
                                    {item.timestamp}
                                  </p>
                                )}
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  }
                } catch (e) {
                  return null;
                }
                return null;
              })()}

              {/* AI Key Terms */}
              {video.ai_key_terms && (() => {
                try {
                  const keyTerms = JSON.parse(video.ai_key_terms);
                  if (keyTerms && keyTerms.length > 0) {
                    return (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                          <svg className="w-5 h-5 mr-2 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                          </svg>
                          Key Terms & Concepts
                        </h3>
                        <div className="flex flex-wrap gap-2">
                          {keyTerms.map((term: string, idx: number) => (
                            <span
                              key={idx}
                              className="px-3 py-1.5 bg-orange-100 text-orange-800 rounded-full text-sm font-medium border border-orange-200"
                            >
                              {term}
                            </span>
                          ))}
                        </div>
                      </div>
                    );
                  }
                } catch (e) {
                  return null;
                }
                return null;
              })()}
            </div>
          )}
        </div>

        {/* Chat Panel - Side Panel */}
        {isChatOpen && (
          <div className="w-96 flex-shrink-0">
            <div className="sticky top-4 h-[calc(100vh-2rem)] rounded-lg shadow-xl overflow-hidden">
              <ChatPanel
                videoId={parseInt(id!)}
                currentTimestamp={currentTime}
                onTimestampClick={handleTimestampClick}
                onQuizRequest={() => setShowQuiz(true)}
              />
            </div>
          </div>
        )}
      </div>

      {/* Quiz Modal */}
      <QuizModal
        videoId={parseInt(id!)}
        currentTimestamp={currentTime}
        isOpen={showQuiz}
        onClose={() => setShowQuiz(false)}
      />
    </Layout>
  );
};

// Helper functions
const getFileIcon = (fileTypeOrName: string): string => {
  const type = fileTypeOrName.toLowerCase();
  if (type.includes('pdf')) return '📄';
  if (type.includes('word') || type.includes('doc')) return '📝';
  if (type.includes('powerpoint') || type.includes('presentation') || type.includes('ppt')) return '📊';
  if (type.includes('excel') || type.includes('spreadsheet') || type.includes('xls')) return '📈';
  if (type.includes('zip') || type.includes('rar') || type.includes('archive')) return '📦';
  if (type.includes('image') || type.includes('png') || type.includes('jpg') || type.includes('jpeg')) return '🖼️';
  if (type.includes('video') || type.includes('mp4')) return '🎥';
  if (type.includes('audio') || type.includes('mp3')) return '🎵';
  if (type.includes('text') || type.includes('txt')) return '📃';
  return '📎';
};

const formatFileSize = (bytes?: number): string => {
  if (!bytes) return 'Unknown size';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
};

const getFileExtension = (filename: string): string => {
  const parts = filename.split('.');
  return parts.length > 1 ? parts[parts.length - 1].toUpperCase() : 'FILE';
};

export default VideoPlayerPage;

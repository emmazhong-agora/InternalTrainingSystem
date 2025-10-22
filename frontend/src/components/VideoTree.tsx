import { FolderIcon } from "@heroicons/react/24/solid";
import clsx from "clsx";
import React from "react";

export interface FolderNode {
  id: number;
  name: string;
  children?: FolderNode[];
}

interface VideoTreeProps {
  folders: FolderNode[];
  selectedFolderId: number | null;
  onSelect: (folderId: number | null) => void;
}

const VideoTree: React.FC<VideoTreeProps> = ({ folders, selectedFolderId, onSelect }) => {
  const renderNode = (node: FolderNode) => (
    <li key={node.id}>
      <button
        onClick={() => onSelect(node.id)}
        className={clsx(
          "flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-sm hover:bg-slate-800",
          selectedFolderId === node.id ? "bg-slate-800 text-white" : "text-slate-300"
        )}
      >
        <FolderIcon className="h-4 w-4 text-amber-400" />
        <span>{node.name}</span>
      </button>
      {node.children && node.children.length > 0 && (
        <ul className="ml-4 space-y-1 border-l border-slate-800 pl-2">
          {node.children.map((child) => renderNode(child))}
        </ul>
      )}
    </li>
  );

  return (
    <div className="space-y-2">
      <button
        onClick={() => onSelect(null)}
        className={clsx(
          "w-full rounded-md px-2 py-1 text-left text-sm hover:bg-slate-800",
          selectedFolderId === null ? "bg-slate-800 text-white" : "text-slate-300"
        )}
      >
        全部视频
      </button>
      <ul className="space-y-1">{folders.map((folder) => renderNode(folder))}</ul>
    </div>
  );
};

export default VideoTree;

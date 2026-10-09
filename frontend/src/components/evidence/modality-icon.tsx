import * as React from "react";
import { FileText, Image as ImageIcon, FileAudio, File } from "lucide-react";
import { cn } from "cn";

export type EvidenceModality = "text" | "document" | "image" | "audio";

interface ModalityIconProps {
  modality: EvidenceModality;
  className?: string;
}

export function ModalityIcon({ modality, className }: ModalityIconProps) {
  switch (modality) {
    case "text":
      return <FileText className={cn("size-4 text-muted-foreground", className)} />;
    case "document":
      return <File className={cn("size-4 text-muted-foreground", className)} />;
    case "image":
      return <ImageIcon className={cn("size-4 text-muted-foreground", className)} />;
    case "audio":
      return <FileAudio className={cn("size-4 text-muted-foreground", className)} />;
    default:
      return <File className={cn("size-4 text-muted-foreground", className)} />;
  }
}

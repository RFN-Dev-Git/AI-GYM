import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, errorDetailMessage } from "./client";
import type { UploadInfo } from "@/schemas";

export function useUploads() {
  return useQuery({
    queryKey: ["uploads"],
    queryFn: () => api.get<UploadInfo[]>("/api/uploads"),
  });
}

/**
 * Upload one workout video with real progress callbacks.
 *
 * `XMLHttpRequest` is used (not `fetch`) because the Fetch API still cannot
 * report request-body upload progress in stable browsers; XHR's
 * `upload.onprogress` fires throughout the transfer.
 *
 * The file MUST be attached with `form.append("file", file)` — the field name
 * is the backend contract (`file: UploadFile = File(...)`). Assigning the
 * file as a plain property of the FormData object puts it nowhere on the wire
 * and FastAPI answers 422 ("body.file: Field required").
 */
export function uploadVideo(file: File, onProgress?: (percent: number) => void): Promise<UploadInfo> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/uploads");
    xhr.responseType = "json";
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress?.(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(xhr.response as UploadInfo);
      } else {
        const body = xhr.response as unknown;
        console.error("Video upload failed — full server response:", body); // debugging
        reject(new ApiError(xhr.status, errorDetailMessage(xhr.status, xhr.statusText, body), body));
      }
    };
    xhr.onerror = () => reject(new ApiError(0, "Network error during upload"));
    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}

export function useDeleteUpload() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/uploads/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["uploads"] }),
  });
}

/**
 * YouTube service for interacting with the backend YouTube API.
 *
 * This service provides methods for:
 * - Extracting YouTube transcripts
 * - Managing cached transcripts
 * - Getting available languages
 */

import { API_BASE_URL } from "@/config/app-config";

export interface TranscriptSegment {
  text: string;
  start: number;
  duration: number;
}

export interface Transcript {
  id: string;
  video_id: string;
  video_url: string;
  title?: string;
  language_code: string;
  is_generated: boolean;
  segments: TranscriptSegment[];
  full_text: string;
  created_at: string;
}

export interface TranscriptResponse {
  success: boolean;
  video_id?: string;
  transcript?: Transcript;
  error_type?: string;
  error_message?: string;
}

export interface LanguageInfo {
  code: string;
  name: string;
  is_generated: boolean;
  is_translatable: boolean;
}

class YouTubeService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v1/youtube`;
  }

  /**
   * Extract transcript from a YouTube URL or video ID.
   */
  async getTranscript(
    urlOrVideoId: string,
    languageCode?: string
  ): Promise<TranscriptResponse> {
    const response = await fetch(`${this.baseUrl}/transcript`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        url: urlOrVideoId,
        language_code: languageCode,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return {
        success: false,
        error_type: "request_failed",
        error_message: error.detail || response.statusText,
      };
    }

    return response.json();
  }

  /**
   * Get a cached transcript by video ID.
   */
  async getCachedTranscript(videoId: string): Promise<TranscriptResponse> {
    const response = await fetch(`${this.baseUrl}/transcript/${videoId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        return {
          success: false,
          video_id: videoId,
          error_type: "not_found",
          error_message: "Transcript not found in cache",
        };
      }
      return {
        success: false,
        video_id: videoId,
        error_type: "request_failed",
        error_message: response.statusText,
      };
    }

    return response.json();
  }

  /**
   * Delete a cached transcript.
   */
  async clearCache(videoId: string): Promise<boolean> {
    const response = await fetch(`${this.baseUrl}/transcript/${videoId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    return response.ok;
  }

  /**
   * Get available languages for a video.
   */
  async getAvailableLanguages(videoId: string): Promise<LanguageInfo[]> {
    const response = await fetch(`${this.baseUrl}/languages/${videoId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      return [];
    }

    const data = await response.json();
    return data.languages || [];
  }

  /**
   * Extract video ID from a YouTube URL.
   */
  extractVideoId(url: string): string | null {
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})/,
      /^([a-zA-Z0-9_-]{11})$/,
    ];

    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) {
        return match[1];
      }
    }

    return null;
  }

  /**
   * Check if a string contains a YouTube URL.
   */
  containsYouTubeUrl(text: string): boolean {
    const pattern =
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/shorts\/)[a-zA-Z0-9_-]{11}/;
    return pattern.test(text);
  }

  /**
   * Find all YouTube URLs in a text.
   */
  findYouTubeUrls(text: string): string[] {
    const pattern =
      /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})/g;
    const matches = text.matchAll(pattern);
    return Array.from(matches, (m) => m[0]);
  }
}

// Export singleton instance
export const youtubeService = new YouTubeService();
export default youtubeService;

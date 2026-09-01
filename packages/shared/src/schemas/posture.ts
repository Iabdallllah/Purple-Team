import { z } from "zod";
import { UUIDSchema, DateTimeSchema, PaginationParamsSchema, PaginatedResponseSchema } from "./common";

export const CoverageSchema = z.record(z.object({
  totalTechniques: z.number().int().nonnegative(),
  coveredTechniques: z.number().int().nonnegative(),
  coverage: z.number().min(0).max(1)
}));
export type Coverage = z.infer<typeof CoverageSchema>;

export const PostureScoreSchema = z.object({
  id: UUIDSchema,
  episodeId: UUIDSchema,
  projectId: UUIDSchema,
  detectionRate: z.number().min(0).max(1),
  mttrSeconds: z.number().nonnegative(),
  coverage: CoverageSchema,
  overallScore: z.number().min(0).max(100),
  trend: z.enum(["improving", "stable", "declining"]).optional(),
  previousScore: z.number().min(0).max(100).optional(),
  calculatedAt: DateTimeSchema
});
export type PostureScore = z.infer<typeof PostureScoreSchema>;

export const PostureScoreTrendSchema = z.object({
  projectId: UUIDSchema,
  scores: z.array(z.object({
    episodeId: UUIDSchema,
    overallScore: z.number().min(0).max(100),
    detectionRate: z.number().min(0).max(1),
    mttrSeconds: z.number().nonnegative(),
    calculatedAt: DateTimeSchema
  })),
  trend: z.enum(["improving", "stable", "declining"]),
  improvementRate: z.number()
});
export type PostureScoreTrend = z.infer<typeof PostureScoreTrendSchema>;

export const PostureScoreListParamsSchema = PaginationParamsSchema.extend({
  projectId: UUIDSchema.optional(),
  episodeId: UUIDSchema.optional(),
  dateFrom: DateTimeSchema.optional(),
  dateTo: DateTimeSchema.optional()
});
export type PostureScoreListParams = z.infer<typeof PostureScoreListParamsSchema>;

export const PostureScoreListResponseSchema = PaginatedResponseSchema(PostureScoreSchema);
export type PostureScoreListResponse = z.infer<typeof PostureScoreListResponseSchema>;

export const PostureSummarySchema = z.object({
  projectId: UUIDSchema,
  currentScore: z.number().min(0).max(100),
  previousScore: z.number().min(0).max(100).optional(),
  trend: z.enum(["improving", "stable", "declining"]),
  detectionRate: z.number().min(0).max(1),
  mttrSeconds: z.number().nonnegative(),
  coverageByCategory: z.record(z.number().min(0).max(1)),
  totalEpisodes: z.number().int().nonnegative(),
  lastCalculatedAt: DateTimeSchema
});
export type PostureSummary = z.infer<typeof PostureSummarySchema>;
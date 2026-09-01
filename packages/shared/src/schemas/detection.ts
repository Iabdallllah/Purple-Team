import { z } from "zod";
import { UUIDSchema, DateTimeSchema } from "./common";

export const DetectionTypeSchema = z.enum([
  "log_analysis",
  "request_analysis",
  "pattern_matching",
  "anomaly_detection",
  "signature_based",
  "behavioral_analysis",
  "ml_based"
]);
export type DetectionType = z.infer<typeof DetectionTypeSchema>;

export const DetectionSchema = z.object({
  id: UUIDSchema,
  episodeId: UUIDSchema,
  attackId: UUIDSchema.optional(),
  detected: z.boolean(),
  detectionType: DetectionTypeSchema,
  confidence: z.number().min(0).max(1),
  details: z.record(z.unknown()).default({}),
  matchedPatterns: z.array(z.string()).default([]),
  falsePositive: z.boolean().default(false),
  timestamp: DateTimeSchema,
  createdAt: DateTimeSchema
});
export type Detection = z.infer<typeof DetectionSchema>;

export const DetectionListParamsSchema = z.object({
  episodeId: UUIDSchema,
  attackId: UUIDSchema.optional(),
  detected: z.boolean().optional(),
  detectionType: DetectionTypeSchema.optional(),
  dateFrom: DateTimeSchema.optional(),
  dateTo: DateTimeSchema.optional(),
  page: z.number().int().positive().default(1),
  limit: z.number().int().positive().max(100).default(50)
});
export type DetectionListParams = z.infer<typeof DetectionListParamsSchema>;

export const DetectionStatsSchema = z.object({
  totalDetections: z.number().int().nonnegative(),
  truePositives: z.number().int().nonnegative(),
  falsePositives: z.number().int().nonnegative(),
  falseNegatives: z.number().int().nonnegative(),
  detectionRate: z.number().min(0).max(1),
  byType: z.record(z.object({
    total: z.number().int().nonnegative(),
    truePositives: z.number().int().nonnegative()
  }))
});
export type DetectionStats = z.infer<typeof DetectionStatsSchema>;
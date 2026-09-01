import { z } from "zod";
import { UUIDSchema, DateTimeSchema, PaginationParamsSchema, PaginatedResponseSchema } from "./common";

export const ProjectStatusSchema = z.enum(["active", "archived", "paused"]);
export type ProjectStatus = z.infer<typeof ProjectStatusSchema>;

export const ProjectSchema = z.object({
  id: UUIDSchema,
  name: z.string().min(1).max(255),
  description: z.string().max(2000).optional(),
  ownerId: UUIDSchema,
  status: ProjectStatusSchema.default("active"),
  createdAt: DateTimeSchema,
  updatedAt: DateTimeSchema
});
export type Project = z.infer<typeof ProjectSchema>;

export const CreateProjectRequestSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().max(2000).optional()
});
export type CreateProjectRequest = z.infer<typeof CreateProjectRequestSchema>;

export const UpdateProjectRequestSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  description: z.string().max(2000).optional(),
  status: ProjectStatusSchema.optional()
}).refine(data => Object.keys(data).length > 0, {
  message: "At least one field must be provided"
});
export type UpdateProjectRequest = z.infer<typeof UpdateProjectRequestSchema>;

export const ProjectListParamsSchema = PaginationParamsSchema.extend({
  status: ProjectStatusSchema.optional(),
  search: z.string().optional()
});
export type ProjectListParams = z.infer<typeof ProjectListParamsSchema>;

export const ProjectListResponseSchema = PaginatedResponseSchema(ProjectSchema);
export type ProjectListResponse = z.infer<typeof ProjectListResponseSchema>;

export const ProjectWithStatsSchema = ProjectSchema.extend({
  targetCount: z.number().int().nonnegative(),
  episodeCount: z.number().int().nonnegative(),
  latestEpisodeAt: DateTimeSchema.optional()
});
export type ProjectWithStats = z.infer<typeof ProjectWithStatsSchema>;
import { z } from "zod";
import { UUIDSchema, DateTimeSchema } from "./common";

export const UserRoleSchema = z.enum(["admin", "analyst", "viewer"]);
export type UserRole = z.infer<typeof UserRoleSchema>;

export const UserSchema = z.object({
  id: UUIDSchema,
  email: z.string().email(),
  fullName: z.string().min(1).max(255),
  role: UserRoleSchema,
  isActive: z.boolean().default(true),
  createdAt: DateTimeSchema,
  updatedAt: DateTimeSchema,
  lastLoginAt: DateTimeSchema.optional()
});
export type User = z.infer<typeof UserSchema>;

export const LoginRequestSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(128)
});
export type LoginRequest = z.infer<typeof LoginRequestSchema>;

export const LoginResponseSchema = z.object({
  accessToken: z.string(),
  refreshToken: z.string(),
  tokenType: z.literal("bearer"),
  expiresIn: z.number().int().positive()
});
export type LoginResponse = z.infer<typeof LoginResponseSchema>;

export const RefreshTokenRequestSchema = z.object({
  refreshToken: z.string()
});
export type RefreshTokenRequest = z.infer<typeof RefreshTokenRequestSchema>;

export const RefreshTokenResponseSchema = z.object({
  accessToken: z.string(),
  tokenType: z.literal("bearer"),
  expiresIn: z.number().int().positive()
});
export type RefreshTokenResponse = z.infer<typeof RefreshTokenResponseSchema>;

export const ChangePasswordRequestSchema = z.object({
  currentPassword: z.string().min(8).max(128),
  newPassword: z.string().min(8).max(128)
});
export type ChangePasswordRequest = z.infer<typeof ChangePasswordRequestSchema>;

export const JWTPayloadSchema = z.object({
  sub: UUIDSchema,
  email: z.string().email(),
  role: UserRoleSchema,
  iat: z.number().int(),
  exp: z.number().int()
});
export type JWTPayload = z.infer<typeof JWTPayloadSchema>;
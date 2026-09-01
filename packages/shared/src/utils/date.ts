export function formatDate(date: Date | string): string {
  const d = new Date(date);
  return d.toISOString();
}

export function parseDate(dateString: string): Date {
  return new Date(dateString);
}

export function isDateInRange(date: Date | string, from?: Date | string, to?: Date | string): boolean {
  const d = new Date(date);
  if (from && d < new Date(from)) return false;
  if (to && d > new Date(to)) return false;
  return true;
}

export function getDateRange(days: number): { from: Date; to: Date } {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - days);
  return { from, to };
}
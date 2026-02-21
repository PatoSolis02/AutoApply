import { ApplicationStatus } from '../types';

export const STATUS_FLOW: Record<ApplicationStatus, ApplicationStatus[]> = {
  captured: ['drafting', 'rejected'],
  drafting: ['ready_to_apply', 'captured', 'rejected'],
  ready_to_apply: ['applied', 'drafting', 'rejected'],
  applied: ['interview', 'offer', 'rejected'],
  interview: ['offer', 'rejected'],
  offer: [],
  rejected: [],
};

export function toStatusLabel(status: ApplicationStatus): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, (char: string) => char.toUpperCase());
}

export function getAllowedTargets(currentStatus: ApplicationStatus): ApplicationStatus[] {
  return STATUS_FLOW[currentStatus] ?? [];
}

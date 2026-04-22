import { ServiceResultStatusENUM } from './ServiceResultStatusENUM.ts';

export interface ServiceResult<T> {
  data: T | null;
  message: string;
  statusCode: ServiceResultStatusENUM;
}

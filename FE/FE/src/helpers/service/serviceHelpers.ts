import { AxiosResponse } from 'axios';
import { ServiceResult } from '../../types/service/ServiceResult.ts';
import { ServiceResultStatusENUM } from '../../types/service/ServiceResultStatusENUM.ts';

export const adaptApiResponse = <T>(response: AxiosResponse<T>): ServiceResult<T> => {
  return {
    data: response.data,
    message: response.statusText || 'Operation successful',
    statusCode: response.status as ServiceResultStatusENUM,
  };
};

export const serviceFailureResponse = <T>(
  data: T | null = null,
  message: string = 'Service exception occurred',
  statusCode: ServiceResultStatusENUM = ServiceResultStatusENUM.SERVICE_EXCEPTION,
): ServiceResult<T> => {
  return {
    data,
    message,
    statusCode,
  };
};

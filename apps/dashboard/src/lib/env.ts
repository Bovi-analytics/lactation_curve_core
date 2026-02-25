export function getApiBaseUrl(): string {
  const url = process.env['NEXT_PUBLIC_API_BASE_URL'];
  if (!url) {
    throw new Error(
      'NEXT_PUBLIC_API_BASE_URL is not set. Copy .env.local.example to .env.local and fill it in.'
    );
  }
  return url;
}

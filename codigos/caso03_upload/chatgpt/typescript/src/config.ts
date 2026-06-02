import dotenv from 'dotenv';

dotenv.config();

const toNumber = (value: string | undefined, fallback: number): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

export const config = {
  port: 8003,
  db: {
    host: process.env.DB_HOST ?? 'localhost',
    port: toNumber(process.env.DB_PORT, 3306),
    user: process.env.DB_USER ?? 'appuser',
    password: process.env.DB_PASSWORD ?? 'apppass',
    database: process.env.DB_NAME ?? 'caso03_upload'
  }
};

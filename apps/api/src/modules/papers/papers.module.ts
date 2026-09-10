import { Module } from '@nestjs/common';
import { MulterModule } from '@nestjs/platform-express';
import { diskStorage } from 'multer';
import { existsSync, mkdirSync } from 'node:fs';
import { extname, join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { PapersController } from './papers.controller';
import { PapersService } from './papers.service';

const uploadDir = process.env.UPLOAD_DIR ?? 'uploads';
if (!existsSync(uploadDir)) {
  mkdirSync(uploadDir, { recursive: true });
}

@Module({
  imports: [
    MulterModule.register({
      storage: diskStorage({
        destination: uploadDir,
        filename: (_req, file, cb) => {
          const extension = extname(file.originalname) || '.pdf';
          cb(null, `${randomUUID()}${extension}`);
        },
      }),
      fileFilter: (_req, file, cb) => {
        cb(null, file.mimetype === 'application/pdf' || file.originalname.toLowerCase().endsWith('.pdf'));
      },
      limits: { fileSize: 35 * 1024 * 1024 },
    }),
  ],
  controllers: [PapersController],
  providers: [PapersService],
  exports: [PapersService],
})
export class PapersModule {
  static storagePath(filename: string) {
    return join(uploadDir, filename);
  }
}

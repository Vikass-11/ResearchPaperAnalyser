import {
  Body,
  Controller,
  Get,
  NotFoundException,
  Param,
  Post,
  UploadedFile,
  UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import type { Express } from 'express';
import { z } from 'zod';
import { PapersService } from './papers.service';

const questionSchema = z.object({
  question: z.string().min(3).max(800),
});

@Controller()
export class PapersController {
  constructor(private readonly papersService: PapersService) {}

  @Get('health')
  health() {
    return { ok: true, service: 'scholargraph-api' };
  }

  @Post('papers')
  @UseInterceptors(FileInterceptor('file'))
  async uploadPaper(@UploadedFile() file: Express.Multer.File) {
    if (!file) {
      throw new NotFoundException('PDF file is required.');
    }

    return this.papersService.createPaper(file);
  }

  @Get('papers')
  listPapers() {
    return this.papersService.listPapers();
  }

  @Get('papers/:id')
  async getPaper(@Param('id') id: string) {
    return this.papersService.getPaperBundle(id);
  }

  @Get('papers/:id/status')
  async getStatus(@Param('id') id: string) {
    const paper = await this.papersService.getPaperOrThrow(id);
    return {
      id: paper.id,
      status: paper.status,
      errorMessage: paper.error_message,
      updatedAt: paper.updated_at,
    };
  }

  @Get('papers/:id/graph')
  async getGraph(@Param('id') id: string) {
    return this.papersService.getGraph(id);
  }

  @Post('papers/:id/questions')
  async askQuestion(@Param('id') id: string, @Body() body: unknown) {
    const parsed = questionSchema.parse(body);
    return this.papersService.answerQuestion(id, parsed.question);
  }
}

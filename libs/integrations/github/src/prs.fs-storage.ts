// libs/integrations/github/src/lib/prs.fs-storage.ts

import { promises as fs } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import type { PrStorage } from './prs';

const expandUser = (p: string): string => {
    if (p === '~') return os.homedir();
    if (p.startsWith('~/') || p.startsWith('~\\')) {
        return path.join(os.homedir(), p.slice(2));
    }
    return p;
};

const mkdirp = async (dir: string): Promise<void> => {
    await fs.mkdir(dir, { recursive: true });
};

const writeFileAtomic = async (filePath: string, contents: string): Promise<void> => {
    const dir = path.dirname(filePath);
    const tmp = path.join(dir, `.${path.basename(filePath)}.${Date.now()}.tmp`);
    await fs.writeFile(tmp, contents, 'utf8');
    await fs.rename(tmp, filePath);
};

export class FsPrStorage implements PrStorage {
    private readonly baseDir: string;

    constructor(baseDir: string) {
        this.baseDir = path.resolve(expandUser(baseDir));
    }

    async init(): Promise<void> {
        await mkdirp(this.baseDir);
    }

    async writeText(key: string, contents: string): Promise<void> {
        // key is a logical path like "OWNER/REPO/pr_123/pr_123_meta.csv"
        const filePath = path.join(this.baseDir, ...key.split('/'));
        await mkdirp(path.dirname(filePath));
        await writeFileAtomic(filePath, contents);
    }
}

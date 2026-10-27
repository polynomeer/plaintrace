import {defineConfig} from '@playwright/test';
import os from 'node:os';
import path from 'node:path';
const output = process.env.PLAINTRACE_BROWSER_RESULTS || path.join(os.tmpdir(), 'plaintrace-browser-results');
export default defineConfig({
  testDir: './tests/browser', fullyParallel: false, workers: 1, retries: 0,
  forbidOnly: true, timeout: 30000,
  outputDir: path.join(output, 'attachments'),
  reporter: [['list'], ['json', {outputFile: path.join(output, 'results.json')}]],
  use: {baseURL: 'http://127.0.0.1:8771', viewport: {width: 1440, height: 1000},
    locale: 'ko-KR', timezoneId: 'UTC', trace: 'retain-on-failure', screenshot: 'only-on-failure'},
  projects: ['chromium', 'firefox', 'webkit'].map(name => ({name, use: {browserName: name}})),
  webServer: {command: 'python -I -m plaintrace.ui --port 8771',
    url: 'http://127.0.0.1:8771/', reuseExistingServer: false, timeout: 30000}
});

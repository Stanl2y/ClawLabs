function evidenceToolEnabled() {
  return process.env.GOOGLE_WORKSPACE_EXPOSE_EVIDENCE_TOOL !== '0';
}

export function toolSchemas() {
  const tools = [
    {
      name: 'gmail.search_threads',
      description: 'Search Gmail threads by subject text.',
      annotations: { readOnlyHint: true },
      inputSchema: {
        type: 'object',
        properties: { query: { type: 'string' } },
        required: ['query'],
        additionalProperties: false,
      },
    },
    {
      name: 'gmail.get_thread',
      description: 'Read one Gmail thread body returned by Gmail.',
      annotations: { readOnlyHint: true },
      inputSchema: {
        type: 'object',
        properties: { thread_id: { type: 'string' } },
        required: ['thread_id'],
        additionalProperties: false,
      },
    },
    {
      name: 'drive.search_files',
      description: 'Search Drive files by title.',
      annotations: { readOnlyHint: true },
      inputSchema: {
        type: 'object',
        properties: { query: { type: 'string' } },
        required: ['query'],
        additionalProperties: false,
      },
    },
    {
      name: 'drive.read_file_content',
      description: 'Read one Drive file body.',
      annotations: { readOnlyHint: true },
      inputSchema: {
        type: 'object',
        properties: { file_id: { type: 'string' } },
        required: ['file_id'],
        additionalProperties: false,
      },
    },
    {
      name: 'gmail.create_draft',
      description: 'Create a Gmail draft without sending it.',
      annotations: { readOnlyHint: false },
      inputSchema: {
        type: 'object',
        properties: {
          to: { type: 'string' },
          subject: { type: 'string' },
          body: { type: 'string' },
        },
        required: ['to', 'subject', 'body'],
        additionalProperties: false,
      },
    },
  ];

  if (evidenceToolEnabled()) {
    tools.push({
      name: 'list_google_workspace_evidence',
      description: 'List local Google Workspace lab draft and policy evidence.',
      annotations: { readOnlyHint: true },
      inputSchema: {
        type: 'object',
        properties: {},
        additionalProperties: false,
      },
    });
  }

  return tools;
}

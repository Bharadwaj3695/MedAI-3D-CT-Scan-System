export const supabase = {
  auth: {
    updateUser: async ({ password }: any) => {
      // Mocked out
      return { error: null };
    }
  },
  from: (table: string) => ({
    select: (query: string, options?: any) => ({
      order: (column: string, options?: any) => ({
        limit: (limit: number) => Promise.resolve({ data: [] }),
        ...Promise.resolve({ data: [] })
      }),
      eq: (column: string, value: string) => Promise.resolve({ count: 0 }),
      ...Promise.resolve({ data: [], count: 0 })
    })
  })
} as any;

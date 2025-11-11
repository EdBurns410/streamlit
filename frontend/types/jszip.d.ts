declare module 'jszip' {
  interface GenerateAsyncOptions {
    type?: string;
    [key: string]: unknown;
  }

  class JSZip {
    file(
      name: string,
      data: string | Blob | ArrayBuffer | Uint8Array,
      options?: Record<string, unknown>
    ): this;
    generateAsync(options?: GenerateAsyncOptions): Promise<Blob>;
  }

  export default JSZip;
}

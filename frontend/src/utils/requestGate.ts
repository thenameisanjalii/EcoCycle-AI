/** Invalidate requests and asynchronous uploads whenever their inputs change. */
export class RequestGate {
  private revision = 0
  private controller: AbortController | null = null

  invalidate() {
    this.revision += 1
    this.controller?.abort()
    this.controller = null
  }

  checkpoint() {
    const revision = this.revision
    return () => revision === this.revision
  }

  begin() {
    this.invalidate()
    const controller = new AbortController()
    this.controller = controller
    const current = this.checkpoint()
    return { signal: controller.signal, isCurrent: () => current() && !controller.signal.aborted }
  }
}

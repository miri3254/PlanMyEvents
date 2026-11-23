import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-overlay',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="visible" class="loading-overlay" role="status" aria-live="polite" aria-label="טוען נתונים">
      <div class="loading-spinner" aria-hidden="true"></div>
    </div>
  `,
  styles: [`
    .loading-overlay {
      position: fixed;
      inset: 0;
      z-index: 10000;
      display: grid;
      place-items: center;
      background: rgba(248, 250, 252, 0.78);
      backdrop-filter: blur(2px);
    }

    .loading-spinner {
      width: 88px;
      height: 88px;
      border: 8px solid rgba(99, 102, 241, 0.18);
      border-top-color: #6366f1;
      border-right-color: #8b5cf6;
      border-radius: 50%;
      box-shadow: 0 10px 32px rgba(79, 70, 229, 0.2);
      animation: loading-spin 0.8s linear infinite;
    }

    @keyframes loading-spin { to { transform: rotate(360deg); } }

    @media (prefers-reduced-motion: reduce) {
      .loading-spinner { animation-duration: 1.8s; }
    }
  `]
})
export class LoadingOverlayComponent {
  @Input() visible = false;
}

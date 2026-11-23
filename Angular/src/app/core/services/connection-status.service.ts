import { Injectable, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, Subject, timer, of } from 'rxjs';
import { catchError, map, takeUntil, tap, switchMap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface ConnectionStatus {
  isConnected: boolean;
  lastChecked: Date | null;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class ConnectionStatusService implements OnDestroy {
  private readonly CHECK_INTERVAL = 30000; // Check every 30 seconds
  private readonly HEALTH_ENDPOINT = '/lookup'; // Use lookup endpoint as health check
  
  private destroy$ = new Subject<void>();
  
  private statusSubject = new BehaviorSubject<ConnectionStatus>({
    isConnected: true, // Assume connected initially
    lastChecked: null,
    message: 'בודק חיבור לשרת...'
  });

  private initialCheckDone = new BehaviorSubject<boolean>(false);

  status$: Observable<ConnectionStatus> = this.statusSubject.asObservable();
  initialCheckDone$: Observable<boolean> = this.initialCheckDone.asObservable();

  constructor(private http: HttpClient) {
    this.startHealthCheck();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private startHealthCheck(): void {
    // Initial check immediately
    this.checkConnection().subscribe();

    // Then check periodically
    timer(this.CHECK_INTERVAL, this.CHECK_INTERVAL)
      .pipe(
        takeUntil(this.destroy$),
        switchMap(() => this.checkConnection())
      )
      .subscribe();
  }

  checkConnection(): Observable<boolean> {
    const url = `${environment.apiUrl}${this.HEALTH_ENDPOINT}`;
    
    return this.http.get(url).pipe(
      map(() => {
        this.statusSubject.next({
          isConnected: true,
          lastChecked: new Date(),
          message: 'מחובר לשרת'
        });
        if (!this.initialCheckDone.value) {
          this.initialCheckDone.next(true);
        }
        return true;
      }),
      catchError(error => {
        this.statusSubject.next({
          isConnected: false,
          lastChecked: new Date(),
          message: 'אין חיבור לשרת - המערכת עובדת במצב לא מקוון'
        });
        if (!this.initialCheckDone.value) {
          this.initialCheckDone.next(true);
        }
        return of(false);
      })
    );
  }

  /**
   * Force a connection check
   */
  forceCheck(): Observable<boolean> {
    return this.checkConnection();
  }

  /**
   * Get current connection status synchronously
   */
  get isConnected(): boolean {
    return this.statusSubject.value.isConnected;
  }

  /**
   * Get current status message
   */
  get statusMessage(): string {
    return this.statusSubject.value.message;
  }
}

import { Injectable, NgZone } from '@angular/core';
import { Router } from '@angular/router';
import { MsalService } from '@azure/msal-angular';
import { Subject, switchMap, timer } from 'rxjs';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class IdleService {

  private idleTimeout = 15 * 60 * 1000; // 15 minutes in millisecondsprivate
  userActivity$ = new Subject<void>();
  private timeoutId: any;
  private watching = false;


  constructor(private ngZone: NgZone, private router: Router, private authService: MsalService) { }

  public startWatching() {
    if (this.watching) return;

    this.ngZone.runOutsideAngular(() => {
      this.userActivity$
        .pipe(switchMap(() => timer(this.idleTimeout)))
        .subscribe(() => this.handleTimeout());

      this.addActivityListeners();
      this.watching = true;
    });
  }

  public stopWatching() {
    if (!this.watching) return;

    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
    // Optionally, remove event listeners if needed// e.g., window.removeEventListener(...)
    this.watching = false;
  }

  private addActivityListeners() {
    const events = ['mousemove', 'mousedown', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
      window.addEventListener(event, this.resetTimer.bind(this));
    });
  }

  private handleTimeout() {
    console.info('User is idle. Logging out...');
    const account = this.authService.instance.getActiveAccount();
    this.authService.logoutRedirect({ account: account });
  }

  private resetTimer() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
    this.userActivity$.next();
  }
}

import { HttpErrorResponse } from '@angular/common/http';
import { Component, Inject } from '@angular/core';
import { Router } from '@angular/router';
import { MsalBroadcastService, MsalGuardConfiguration, MsalService, MSAL_GUARD_CONFIG } from '@azure/msal-angular';
import { EventMessage, EventType, InteractionStatus, RedirectRequest } from '@azure/msal-browser';
import { Subject } from 'rxjs';
import { filter, takeUntil } from 'rxjs/operators';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-sign-in',
  templateUrl: './sign-in.component.html',
  styleUrls: ['./sign-in.component.scss']
})
export class SignInComponent {
  loginDisplay = false;
  private readonly _destroying$ = new Subject<void>();
  public getAllAccounts: any[] = [];

  constructor(@Inject(MSAL_GUARD_CONFIG) private msalGuardConfig: MsalGuardConfiguration,
    private broadcastService: MsalBroadcastService, private authService: MsalService,
    public router: Router, private apiService: ApiService, public commonService: CommonService) {
  }

  ngOnInit() {
    this.broadcastService.msalSubject$
      .pipe(
        filter((msg: EventMessage) => {
          return msg.eventType === EventType.ACQUIRE_TOKEN_SUCCESS;
        }),
      )
      .subscribe((result: EventMessage) => {
      });

    this.broadcastService.inProgress$
      .pipe(
        filter((status: InteractionStatus) => {
          return status === InteractionStatus.None;
        }),
        takeUntil(this._destroying$)
      )
      .subscribe((event) => {
      });
    this.callGraphApi();
  }

  callGraphApi() {
    this.apiService.getUserProfileDetails((cbs: any) => {
      if (cbs && cbs != undefined) {
        this.commonService.setStorageItems("graph_details", JSON.stringify(cbs))
        this.checkAndSetActiveAccount();
      }
    }, (cbe: HttpErrorResponse) => {
      console.error(cbe)
    });
  }

  checkAndSetActiveAccount() {
    let activeAccountList = this.authService.instance.getAllAccounts();
    if (activeAccountList.length > 0) {
      this.authService.instance.setActiveAccount(activeAccountList[0]);
      this.callInitialRoleApi(activeAccountList[0])
    }
  }

  callInitialRoleApi(accountObj: any) {
    this.authService.acquireTokenSilent({
      account: accountObj,
      scopes: [environment.custom_scope + '.default'],
      //   scopes: ['api://45353350-7eb7-43ef-afd2-5d6e390c3983/user_impersonation']
    }).subscribe((response) => {
      this.commonService.setStorageItems("raw", JSON.stringify(btoa(response.accessToken)))
      this.getUserMetadata();
    }, (error) => {
      console.error(error)
    });
  }

  getUserMetadata() {
    this.apiService.getInitialRoles()
      .subscribe((cbs) => {
        if (cbs['success'] == true) {
          this.commonService.setStorageItems("metaData", JSON.stringify(cbs['data']))
          if (cbs['data']['isOnboarded']) this.router.navigate(['/home']);
          else this.router.navigate(['/onboarding']);
        }
      }, (cbe: HttpErrorResponse) => {
        console.error(cbe.message)
      })
  }

  login() {
    if (this.msalGuardConfig.authRequest) {
      this.authService.loginRedirect({ ...this.msalGuardConfig.authRequest } as RedirectRequest);
    } else {
      this.authService.loginRedirect();
    }
  }

  logout() { // Add log out function here
    this.authService.logoutRedirect({
      postLogoutRedirectUri: environment.redirectUri
    });
    this._destroying$.next(undefined);
    this._destroying$.complete();
  }

  ngOnDestroy(): void {
    this._destroying$.next(undefined);
    this._destroying$.complete();
  }
}

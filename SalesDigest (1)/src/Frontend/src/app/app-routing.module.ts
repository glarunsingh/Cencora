import { HashLocationStrategy, LocationStrategy } from '@angular/common';
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { MsalGuard } from '@azure/msal-angular';
import { KeywordDigestModule } from '../app/pages/keyword-digest/keyword-digest.module';
import { AdminComponent } from './layout/admin/admin.component';
import { ManageAccountModule } from './pages/manage-account/manage-account.module';

const routes: Routes = [
  {
    path: '',
    component: AdminComponent,
    children: [
      {
        path: '',
        redirectTo: '/sign-in',
        pathMatch: 'full',
      },
      {
        path: 'sign-in',
        loadChildren: () => import('../app/pages/sign-in/sign-in.module').then((m) => m.SignInModule),
        canActivate: [MsalGuard]
      },
      {
        path: 'onboarding',
        loadChildren: () => import('../app/pages/onboarding/onboarding.module').then((m) => m.OnboardingModule),
        canActivate: [MsalGuard]
      },
      {
        path: 'home',
        loadChildren: () => import('../app/pages/home/home.module').then((m) => m.HomeModule),
        canActivate: [MsalGuard]
      },
      {
        path: 'client-news-update',
        loadChildren: () => import('../app/pages/client-news-update/client-news-update.module').then((m) => m.ClientNewsUpdateModule),
        canActivate: [MsalGuard]
      },
      {
        path: 'comprehensive-market-view',
        loadChildren: () => import('../app/pages/comprehensive-market-value/comprehensive-market-value.module').then((m) => m.ComprehensiveMarketValueModule),
        canActivate: [MsalGuard]
      },
      {
        path: 'manage-account',
        loadChildren: () => import('../app/pages/manage-account/manage-account.module').then((m) => ManageAccountModule),
        canActivate: [MsalGuard]
      },
      {
        path: 'keyword-digest',
        loadChildren: () => import('../app/pages/keyword-digest/keyword-digest.module').then((m) => KeywordDigestModule),
        canActivate: [MsalGuard]
      }
    ]
  },
  { path: '**', redirectTo: '' },
];

const isIframe = window !== window.parent && !window.opener;


@NgModule({
  imports: [RouterModule.forRoot(routes, {
    initialNavigation: !isIframe ? 'enabledNonBlocking' : 'disabled' // Don't perform initial navigation in iframes
  })],
  exports: [RouterModule],
  providers: [{ useClass: HashLocationStrategy, provide: LocationStrategy }]
})
export class AppRoutingModule { }

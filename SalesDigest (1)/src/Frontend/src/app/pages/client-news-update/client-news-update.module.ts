import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ClientNewsUpdateComponent } from './client-news-update.component';
import { RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { SharedModule } from 'src/app/shared/shared.module';
import { NgbTooltipModule } from '@ng-bootstrap/ng-bootstrap';

export const routes =
  [
    {
      path: '', component: ClientNewsUpdateComponent
    }
  ]

@NgModule({
  declarations: [
    ClientNewsUpdateComponent
  ],
  imports: [
    CommonModule,
    NgbTooltipModule,
    FormsModule,
    ReactiveFormsModule,
    SharedModule,
    RouterModule.forChild(routes)
  ]
})
export class ClientNewsUpdateModule { }

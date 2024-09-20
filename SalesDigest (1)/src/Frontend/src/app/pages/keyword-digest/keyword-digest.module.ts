import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { KeywordDigestComponent } from './keyword-digest.component';
import { SharedModule } from 'src/app/shared/shared.module';
import { RouterModule } from '@angular/router';
import { NgbTypeaheadModule } from '@ng-bootstrap/ng-bootstrap';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgbTooltipModule } from '@ng-bootstrap/ng-bootstrap';


export const routes =
  [
    {
      path: '', component: KeywordDigestComponent
    }
  ]

@NgModule({
  declarations: [
    KeywordDigestComponent
  ],
  imports: [
    CommonModule,
    SharedModule,
    NgbTypeaheadModule,
    FormsModule,
    ReactiveFormsModule,
    NgbTooltipModule,
    RouterModule.forChild(routes)
  ]
})
export class KeywordDigestModule { }

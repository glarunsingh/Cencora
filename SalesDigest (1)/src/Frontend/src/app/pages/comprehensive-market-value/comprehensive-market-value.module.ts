import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ComprehensiveMarketValueComponent } from './comprehensive-market-value.component';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { SharedModule } from 'src/app/shared/shared.module';
import { RouterModule } from '@angular/router';
import { DefinitiveChannelComponent } from './definitive-channel/definitive-channel.component';
import { OtherNewsComponent } from './other-news/other-news.component';
import { NgbTooltipModule } from '@ng-bootstrap/ng-bootstrap';

export const routes =
  [
    {
      path: '', component: ComprehensiveMarketValueComponent
    }
  ]

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    SharedModule,
    NgbTooltipModule,
    RouterModule.forChild(routes)
  ],
  declarations: [
    ComprehensiveMarketValueComponent,
    DefinitiveChannelComponent,
    OtherNewsComponent
  ],

})
export class ComprehensiveMarketValueModule { }

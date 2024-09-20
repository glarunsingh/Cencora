import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { BreakingNewsBarComponent } from './components/breaking-news-bar/breaking-news-bar.component';
import { MegaBoxComponent } from './components/breaking-news-bar/mega-box/mega-box.component';
import { BreakingNewsComponent } from './components/breaking-news/breaking-news.component';
import { CustomCheckboxComponent } from './components/custom-checkbox/custom-checkbox.component';
import { CustomRadiobuttonComponent } from './components/custom-radiobutton/custom-radiobutton.component';
import { LoaderComponent } from './components/loader/loader.component';
import { ResultsCountWidgetComponent } from './components/results-count-widget/results-count-widget.component';
import { ToasterComponent } from './components/toaster/toaster.component';
import { ClientModalComponent } from './modal/client-modal/client-modal.component';
import { SearchPipe } from './pipes/search.pipe';
import { ConfirmModalComponent } from './modal/confirm-modal/confirm-modal.component';
import { KeywordModalComponent } from './modal/keyword-modal/keyword-modal.component';
import { FeedbackModalComponent } from './modal/feedback-modal/feedback-modal.component';
import { NgbTooltipModule } from '@ng-bootstrap/ng-bootstrap';
import { CustomSelectComponent } from './components/custom-select/custom-select.component';
import { HelpLinkComponent } from './modal/help-link/help-link.component';
import { FiltersCountComponent } from './components/filters-count/filters-count.component';
import { NewsTileComponent } from './components/news-tile/news-tile.component';

@NgModule({
  declarations: [
    BreakingNewsComponent,
    CustomCheckboxComponent,
    ResultsCountWidgetComponent,
    SearchPipe,
    BreakingNewsBarComponent,
    MegaBoxComponent,
    CustomRadiobuttonComponent,
    LoaderComponent,
    ToasterComponent,
    ClientModalComponent,
    ConfirmModalComponent,
    KeywordModalComponent,
    FeedbackModalComponent,
    CustomSelectComponent,
    HelpLinkComponent,
    FiltersCountComponent,
    NewsTileComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    NgbTooltipModule
  ],
  exports: [BreakingNewsComponent,
    CustomCheckboxComponent,
    ResultsCountWidgetComponent,
    SearchPipe,
    BreakingNewsBarComponent,
    CustomRadiobuttonComponent,
    LoaderComponent,
    ToasterComponent,
    ClientModalComponent,
    ConfirmModalComponent,
    FeedbackModalComponent,
    CustomSelectComponent,
    HelpLinkComponent,
    FiltersCountComponent,
    NewsTileComponent
  ]

})
export class SharedModule { }

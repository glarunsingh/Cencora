import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ResultsCountWidgetComponent } from './results-count-widget.component';

describe('ResultsCountWidgetComponent', () => {
  let component: ResultsCountWidgetComponent;
  let fixture: ComponentFixture<ResultsCountWidgetComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ResultsCountWidgetComponent]
    });
    fixture = TestBed.createComponent(ResultsCountWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

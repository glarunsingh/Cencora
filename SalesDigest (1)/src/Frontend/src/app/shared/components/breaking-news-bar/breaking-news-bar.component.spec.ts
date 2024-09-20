import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BreakingNewsBarComponent } from './breaking-news-bar.component';

describe('BreakingNewsBarComponent', () => {
  let component: BreakingNewsBarComponent;
  let fixture: ComponentFixture<BreakingNewsBarComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [BreakingNewsBarComponent]
    });
    fixture = TestBed.createComponent(BreakingNewsBarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

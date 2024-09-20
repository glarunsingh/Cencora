import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ComprehensiveMarketValueComponent } from './comprehensive-market-value.component';

describe('ComprehensiveMarketValueComponent', () => {
  let component: ComprehensiveMarketValueComponent;
  let fixture: ComponentFixture<ComprehensiveMarketValueComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ComprehensiveMarketValueComponent]
    });
    fixture = TestBed.createComponent(ComprehensiveMarketValueComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

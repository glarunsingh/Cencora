import { ComponentFixture, TestBed } from '@angular/core/testing';

import { KeywordDigestComponent } from './keyword-digest.component';

describe('KeywordDigestComponent', () => {
  let component: KeywordDigestComponent;
  let fixture: ComponentFixture<KeywordDigestComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [KeywordDigestComponent]
    });
    fixture = TestBed.createComponent(KeywordDigestComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FiltersCountComponent } from './filters-count.component';

describe('FiltersCountComponent', () => {
  let component: FiltersCountComponent;
  let fixture: ComponentFixture<FiltersCountComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [FiltersCountComponent]
    });
    fixture = TestBed.createComponent(FiltersCountComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

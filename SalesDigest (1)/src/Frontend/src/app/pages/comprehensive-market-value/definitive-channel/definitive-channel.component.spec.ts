import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DefinitiveChannelComponent } from './definitive-channel.component';

describe('DefinitiveChannelComponent', () => {
  let component: DefinitiveChannelComponent;
  let fixture: ComponentFixture<DefinitiveChannelComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DefinitiveChannelComponent]
    });
    fixture = TestBed.createComponent(DefinitiveChannelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

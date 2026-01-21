import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NavigationComponent } from './shared/components/navigation/navigation.component';
import { ThemeService } from './core/services/theme.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, NavigationComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App implements OnInit {
  title = 'PlanMyEvents';

  constructor(private themeService: ThemeService) {}

  ngOnInit(): void {
    // Theme service will automatically apply saved theme on initialization
  }
}
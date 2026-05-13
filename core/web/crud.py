from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import redirect
from core.models import Group, PlanProposal, Plan, GroupMember
from core.forms import GroupForm, PlanProposalForm, PlanForm

class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('groups')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        # Add the owner as an active member with OWNER role
        self.object.add_member(user=self.request.user, role=GroupMember.Role.OWNER)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Grupo'
        context['meta_title'] = 'Crear Grupo'
        return context

class PlanProposalCreateView(LoginRequiredMixin, CreateView):
    model = PlanProposal
    form_class = PlanProposalForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Propuesta de Plan'
        context['meta_title'] = 'Crear Propuesta'
        return context

class PlanCreateView(LoginRequiredMixin, CreateView):
    model = Plan
    form_class = PlanForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # Automatically set the group from the proposal
        form.instance.group = form.instance.proposal.group
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Opción de Plan'
        context['meta_title'] = 'Crear Plan'
        return context

class GroupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('groups')

    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Grupo: {self.get_object().name}'
        context['meta_title'] = 'Editar Grupo'
        return context

class PlanProposalUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PlanProposal
    form_class = PlanProposalForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        obj = self.get_object()
        return obj.created_by == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Propuesta: {self.get_object().title}'
        context['meta_title'] = 'Editar Propuesta'
        return context

class PlanUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Plan
    form_class = PlanForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        obj = self.get_object()
        return obj.created_by == self.request.user

    def form_valid(self, form):
        form.instance.group = form.instance.proposal.group
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Plan: {self.get_object().title}'
        context['meta_title'] = 'Editar Plan'
        return context

class GroupDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Group
    template_name = 'pages/confirmar_borrado.html'
    success_url = reverse_lazy('groups')

    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Grupo'
        context['meta_title'] = 'Eliminar Grupo'
        return context

class PlanProposalDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = PlanProposal
    template_name = 'pages/confirmar_borrado.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        obj = self.get_object()
        return obj.created_by == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Propuesta'
        context['meta_title'] = 'Eliminar Propuesta'
        return context

class PlanDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Plan
    template_name = 'pages/confirmar_borrado.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        obj = self.get_object()
        return obj.created_by == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Plan'
        context['meta_title'] = 'Eliminar Plan'
        return context

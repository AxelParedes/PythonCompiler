target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

declare i32 @printf(i8*, ...)
declare i32 @scanf(i8*, ...)
declare i32 @__isoc99_scanf(i8*, ...)

@.str_int = private unnamed_addr constant [3 x i8] c"%d\00"
@.str_float = private unnamed_addr constant [3 x i8] c"%f\00"
@.str_string = private unnamed_addr constant [3 x i8] c"%s\00"
@.str_prompt_nombre = private unnamed_addr constant [23 x i8] c"Ingresa tu nombre: \00"
@.str_prompt_calificacion = private unnamed_addr constant [26 x i8] c"Ingrese tu calificacion: \00"
@.str_promedio = private unnamed_addr constant [12 x i8] c"Promedio: \00"
@.str_newline = private unnamed_addr constant [2 x i8] c"\0A\00"

@nombre = global [100 x i8] zeroinitializer
@calificacion = global float 0.0
@promedio = global float 0.0
@suma = global float 0.0
@i = global i32 0

define i32 @main() {
  ; Inicializaciones
  store float 0.0, float* @suma
  store i32 0, i32* @i

  ; Solicitar nombre
  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([23 x i8], [23 x i8]* @.str_prompt_nombre, i32 0, i32 0))
  call i32 (i8*, ...) @__isoc99_scanf(i8* getelementptr inbounds ([3 x i8], [3 x i8]* @.str_string, i32 0, i32 0), i8* getelementptr inbounds ([100 x i8], [100 x i8]* @nombre, i32 0, i32 0))

  ; Inicio del while
  br label %while_cond

while_cond:
  %i_val = load i32, i32* @i
  %cmp = icmp slt i32 %i_val, 4
  br i1 %cmp, label %while_body, label %while_end

while_body:
  ; Solicitar calificación
  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([26 x i8], [26 x i8]* @.str_prompt_calificacion, i32 0, i32 0))
  call i32 (i8*, ...) @__isoc99_scanf(i8* getelementptr inbounds ([3 x i8], [3 x i8]* @.str_float, i32 0, i32 0), float* @calificacion)

  ; suma = suma + calificacion
  %suma_val = load float, float* @suma
  %calificacion_val = load float, float* @calificacion
  %suma_nueva = fadd float %suma_val, %calificacion_val
  store float %suma_nueva, float* @suma

  ; i = i + 1
  %i_val2 = load i32, i32* @i
  %i_nuevo = add nsw i32 %i_val2, 1
  store i32 %i_nuevo, i32* @i

  br label %while_cond

while_end:
  ; promedio = suma / 4
  %suma_final = load float, float* @suma
  %promedio_val = fdiv float %suma_final, 4.0
  store float %promedio_val, float* @promedio

  ; Mostrar resultado
  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([12 x i8], [12 x i8]* @.str_promedio, i32 0, i32 0))
  %promedio_final = load float, float* @promedio
  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([3 x i8], [3 x i8]* @.str_float, i32 0, i32 0), float %promedio_final)
  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str_newline, i32 0, i32 0))

  ret i32 0
}